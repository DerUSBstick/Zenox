from __future__ import annotations

import asyncio
import contextlib
import discord
import datetime
import os
import aiohttp

from typing import TYPE_CHECKING, cast

from zenox.constants import ENKA_API_URLS, SIGNATURE_LOC, NICKNAME_LOC
from zenox.enums import Game
from zenox.db.classes import LinkingEntryTemplate, GameAccountTemplate, EnkaOwner, UserConfig
from zenox.db.mongodb import DB
from zenox.embeds import DefaultEmbed
from zenox.bot.error_handler import get_error_embed

if TYPE_CHECKING:
    from zenox.bot import Zenox
    from zenox.embeds import Embed

class LinkingCache:
    MAX_ENTRIES = 75
    ENTRY_TIMEOUT = datetime.timedelta(minutes=15)
    CHECK_INTERVAL_SECONDS = 15
    HOYOLAB_FINALIZE_ENDPOINT = "https://bbs-api-os.hoyolab.com/community/painter/wapi/user/full"
    REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=5)
    HOYOLAB_HEADERS = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "origin": "https://www.hoyolab.com",
        "referer": "https://www.hoyolab.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    }

    def __init__(self) -> None:
        self._entries: list[LinkingEntryTemplate] = []
        self._queue: asyncio.Queue[LinkingEntryTemplate] = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._check_task: asyncio.Task[None] | None = None
        self._finalize_task: asyncio.Task[None] | None = None

    @property
    def is_cache_full(self) -> bool:
        return len(self._entries) >= self.MAX_ENTRIES

    @property
    def is_running(self) -> bool:
        return self._check_task is not None and self._finalize_task is not None

    def start(self) -> None:
        if self.is_running:
            return
        self._check_task = asyncio.create_task(self._check_loop(), name="linking-cache-check")
        self._finalize_task = asyncio.create_task(self._finalize_loop(), name="linking-cache-finalize")

    async def stop(self) -> None:
        tasks_to_cancel = [task for task in (self._check_task, self._finalize_task) if task is not None]
        self._check_task = None
        self._finalize_task = None

        for task in tasks_to_cancel:
            task.cancel()
        if tasks_to_cancel:
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

    def is_user_linked(self, user_id: int) -> bool:
        return any(entry.user_id == user_id for entry in self._entries)

    async def uid_is_already_linked(self, uid: str, game: Game, user_id: int) -> int:
        """0 = not linked, 1 = linked to another user, 2 = linked to user."""
        doc = await DB.accounts.find_one({"uid": uid, "game": game.value})
        if doc is None:
            return 0
        if doc["user_id"] != user_id:
            return 1
        return 2

    def is_uid_linking(self, data: list[tuple[str, Game]]) -> list[tuple[str, Game]]:
        active_pairs = {
            (uid, game)
            for entry in self._entries
            for uid, game in entry.data
        }
        return [(uid, game) for uid, game in data if (uid, game) in active_pairs]

    async def add_entry(self, entry: LinkingEntryTemplate) -> bool:
        if not self.is_running:
            self.start()

        if self.is_cache_full:
            return False

        async with self._lock:
            if self.is_user_linked(entry.user_id):
                return False
            self._entries.append(entry)
        return True

    def get_entries(self) -> list[LinkingEntryTemplate]:
        return self._entries.copy()

    async def remove_entry(self, entry: LinkingEntryTemplate) -> None:
        async with self._lock:
            if entry in self._entries:
                self._entries.remove(entry)

    async def _check_loop(self) -> None:
        try:
            while True:
                await self._check_entries_once()
                await asyncio.sleep(self.CHECK_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            raise

    async def _finalize_loop(self) -> None:
        try:
            while True:
                entry = await self._queue.get()
                try:
                    await self._finalize_entry(entry)
                finally:
                    self._queue.task_done()
        except asyncio.CancelledError:
            raise

    async def _check_entries_once(self) -> None:
        for entry in self.get_entries():
            try:
                expired = entry.started < discord.utils.utcnow() - self.ENTRY_TIMEOUT
                if expired:
                    await self._safe_edit_entry_message(
                        entry,
                        DefaultEmbed(
                            locale=entry.interaction.locale,
                            title="Linking expired",
                            description="Your linking session expired. Please start again.",
                        ),
                    )
                    await self.remove_entry(entry)
                    continue

                if entry.method == "UID":
                    await self._handle_uid_entry(entry)
                elif entry.method == "Hoyolab":
                    await self._handle_hoyolab_entry(entry)
            except Exception as error:
                embed, recognized = get_error_embed(error, entry.interaction.locale)
                if not recognized:
                    self._get_bot(entry).capture_exception(error)

                await self._safe_edit_entry_message(entry, embed)
                await self.remove_entry(entry)

    async def _handle_uid_entry(self, entry: LinkingEntryTemplate) -> None:
        uid, game = entry.data[0]
        response_json = await self._fetch_enka(entry, uid, game)

        signature = self._extract_nested(response_json, SIGNATURE_LOC[game], default="")
        if str(entry.code) not in signature:
            return

        await self._persist_account(entry, uid, game, response_json)
        await self._safe_edit_entry_message(
            entry,
            DefaultEmbed(
                locale=entry.interaction.locale,
                title="Linking successful",
                description="Your UID has been linked successfully.",
            ),
        )
        await self.remove_entry(entry)

    async def _handle_hoyolab_entry(self, entry: LinkingEntryTemplate) -> None:
        if entry.hoyolab_id is None:
            raise ValueError("hoyolab_id is required for Hoyolab linking")

        payload = await self._fetch_hoyolab_profile(entry, entry.hoyolab_id)
        intro = self._extract_nested(payload, ["data", "user_info", "introduce"], default="")
        if str(entry.code) not in intro:
            return

        await self._safe_edit_entry_message(
            entry,
            DefaultEmbed(
                locale=entry.interaction.locale,
                title="Verification successful",
                description="Code detected on your Hoyolab profile. Finalizing linked accounts...",
            ),
        )
        await self._queue.put(entry)
        await self.remove_entry(entry)

    async def _finalize_entry(self, entry: LinkingEntryTemplate) -> None:
        for uid, game in entry.data:
            response_json = await self._fetch_enka(entry, uid, game)
            await self._persist_account(entry, uid, game, response_json)

        await self._safe_edit_entry_message(
            entry,
            DefaultEmbed(
                locale=entry.interaction.locale,
                title="Linking completed",
                description="Your accounts were linked successfully.",
            ),
        )

    async def _fetch_enka(self, entry: LinkingEntryTemplate, uid: str, game: Game) -> dict:
        session = self._get_bot(entry).session
        if session is None:
            raise RuntimeError("Bot HTTP session is not available")
        url = ENKA_API_URLS[game].format(uid=uid)

        async with session.get(url, timeout=self.REQUEST_TIMEOUT) as response:
            payload = await response.json()
            if response.status != 200:
                raise RuntimeError(f"Enka API request failed with status {response.status}")
            return payload

    async def _fetch_hoyolab_profile(self, entry: LinkingEntryTemplate, hoyolab_id: str) -> dict:
        session = self._get_bot(entry).session
        if session is None:
            raise RuntimeError("Bot HTTP session is not available")
        cookies = self._parse_cookie(os.getenv("HOYOLAB_COOKIES", ""))

        async with session.post(
            self.HOYOLAB_FINALIZE_ENDPOINT,
            timeout=self.REQUEST_TIMEOUT,
            json={"scene": 1, "uid": hoyolab_id},
            cookies=cookies,
            headers=self.HOYOLAB_HEADERS,
        ) as response:
            payload = await response.json()
            if response.status != 200 or payload.get("retcode") != 0:
                retcode = payload.get("retcode")
                raise RuntimeError(f"Hoyolab API request failed (status={response.status}, retcode={retcode})")
            return payload

    async def _persist_account(self, entry: LinkingEntryTemplate, uid: str, game: Game, response_json: dict) -> None:
        linked_state = await self.uid_is_already_linked(uid=uid, game=game, user_id=entry.user_id)
        if linked_state == 1:
            raise RuntimeError(f"UID {uid} is already linked to another user")
        if linked_state == 2:
            return

        nickname = self._extract_nested(response_json, NICKNAME_LOC[game], default=uid)
        owner = None
        owner_data = response_json.get("owner")
        if owner_data:
            owner = EnkaOwner(userhash=owner_data["hash"], username=owner_data["username"])

        account = GameAccountTemplate(
            uid=uid,
            game=game,
            username=str(nickname),
            public=True,
            linked_date=discord.utils.utcnow(),
            user_id=entry.user_id,
            hoyolab_id=entry.hoyolab_id,
            enka_owner=owner,
        )

        user = await UserConfig.new(entry.user_id)
        await user._add_account(game, account)

    async def _safe_edit_entry_message(self, entry: LinkingEntryTemplate, embed: Embed) -> None:
        message = entry.interaction.message
        if message is None:
            return

        with contextlib.suppress(discord.NotFound):
            await entry.interaction.followup.edit_message(
                message_id=message.id,
                embed=embed,
                view=None,
            )

    @staticmethod
    def _get_bot(entry: LinkingEntryTemplate) -> Zenox:
        return cast("Zenox", entry.interaction.client)

    @staticmethod
    def _parse_cookie(raw_cookie: str) -> dict[str, str]:
        cookies: dict[str, str] = {}
        for part in raw_cookie.split(";"):
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key:
                cookies[key] = value
        return cookies

    @staticmethod
    def _extract_nested(data: dict, path: list[str], *, default: str | None = None):
        current = data
        for key in path:
            if not isinstance(current, dict) or key not in current:
                if default is None:
                    raise KeyError(f"Missing key path: {'/'.join(path)}")
                return default
            current = current[key]
        return current


linking_cache = LinkingCache()