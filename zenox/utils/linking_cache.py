from __future__ import annotations

import asyncio
import datetime
import contextlib
import logging

import discord

from discord.ext import tasks
from typing import TYPE_CHECKING

from zenox.constants import NICKNAME_LOC, SIGNATURE_LOC
from zenox.enums import PrintColors, Game
from zenox.db.classes import LinkingEntryTemplate, GameAccountTemplate, EnkaOwner, UserConfig
from zenox.db.mongodb import DB
from zenox.clients.linking import LinkingClient

if TYPE_CHECKING:
    from zenox.bot import Zenox

__all__ = ("LinkingCacheManager",)

logger = logging.getLogger(__name__)

_MAX_CACHE_SIZE = 75
_ENTRY_TTL_MINUTES = 15
#: Minimum time between consecutive API polls for the same entry.
_CHECK_INTERVAL_SECONDS = 300  # 5 minutes


class LinkingCacheManager:

    def __init__(self, client: Zenox) -> None:
        self.client = client
        self._linking_cache: list[LinkingEntryTemplate] = []
        self._lock = asyncio.Lock()
        self._queue: asyncio.Queue[LinkingEntryTemplate] = asyncio.Queue()
        self._linking_client = LinkingClient()

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """Start background tasks. Call from ``bot.setup_hook``."""
        self._linking_client.start()
        self._finalize_entries.start()
        self._check_entries.start()
        print(
            f"[LinkingCache] Info - {PrintColors.OKGREEN}Background tasks started.{PrintColors.ENDC}"
        )

    async def stop(self) -> None:
        """Cancel background tasks and close HTTP client. Call from ``bot.close``."""
        self._finalize_entries.cancel()
        self._check_entries.cancel()
        await self._linking_client.close()

    # ------------------------------------------------------------------ #
    # Public helpers                                                       #
    # ------------------------------------------------------------------ #

    @property
    def is_cache_full(self) -> bool:
        return len(self._linking_cache) >= _MAX_CACHE_SIZE

    def is_user_linking(self, user_id: int) -> bool:
        return any(e.user_id == user_id for e in self._linking_cache)

    def get_linking_uids(
        self, data: list[tuple[str, Game]]
    ) -> list[tuple[str, Game]]:
        """Return which (uid, game) pairs from *data* are already in a linking session."""
        result = []
        for uid, game in data:
            for entry in self._linking_cache:
                if any(uid == u and game == g for u, g in entry.data):
                    result.append((uid, game))
                    break
        return result

    async def add_entry(self, entry: LinkingEntryTemplate) -> None:
        async with self._lock:
            self._linking_cache.append(entry)

    async def remove_entry(self, entry: LinkingEntryTemplate) -> None:
        async with self._lock:
            with contextlib.suppress(ValueError):
                self._linking_cache.remove(entry)

    def get_entries(self) -> list[LinkingEntryTemplate]:
        return self._linking_cache.copy()

    async def uid_is_already_linked(self, uid: str, game: Game, user_id: int) -> int:
        """Check whether *uid* is already linked.

        Returns:
            0 — not linked to anyone.
            1 — linked to a different user.
            2 — already linked to *user_id*.
        """
        doc = await DB.accounts.find_one({"uid": uid, "game": game.value})
        if doc is None:
            return 0
        return 2 if doc["user_id"] == user_id else 1

    # ------------------------------------------------------------------ #

    async def _fetch_enka(self, uid: str, game: Game) -> dict:
        """Fetch Enka Network data via the linking client (cached)."""
        return await self._linking_client.fetch_enka(uid, game)

    @staticmethod
    def _extract_nested(data: dict, keys: list[str]) -> str:
        """Walk a nested dict using *keys* and return the string leaf value."""
        value = data
        for k in keys:
            value = value[k]  # type: ignore[assignment]
        return str(value)

    # ------------------------------------------------------------------ #
    # Internal: account creation                                          #
    # ------------------------------------------------------------------ #

    async def _persist_account(
        self,
        entry: LinkingEntryTemplate,
        uid: str,
        game: Game,
        nickname: str,
        enka_owner: EnkaOwner | None,
    ) -> None:
        """Create and persist a ``GameAccountTemplate`` for the given UID."""
        account = GameAccountTemplate(
            uid=uid,
            game=game,
            username=nickname,
            public=True,
            linked_date=discord.utils.utcnow(),
            user_id=entry.user_id,
            hoyolab_id=entry.hoyolab_id,
            enka_owner=enka_owner,
        )
        user = await UserConfig.new(entry.user_id)
        await user._add_account(game, account)

    # ------------------------------------------------------------------ #
    # Background task: finalize verified entries                          #
    # ------------------------------------------------------------------ #

    @tasks.loop(seconds=10)
    async def _finalize_entries(self) -> None:
        """Drain the queue of verified entries and persist their accounts to DB."""
        while not self._queue.empty():
            entry = await self._queue.get()

            if entry.method != "Enka":
                continue  # Only Enka entries use the queue

            finished_title = "linking.enka.finished.title"
            finished_desc = "linking.enka.finished.description"

            failed = False
            for uid, game in entry.data:
                try:
                    data = await self._fetch_enka(uid, game)
                    nickname = self._extract_nested(data, NICKNAME_LOC[game])
                    enka_owner: EnkaOwner | None = None
                    if data.get("owner"):
                        enka_owner = EnkaOwner(
                            userhash=data["owner"]["hash"],
                            username=data["owner"]["username"],
                        )
                    await self._persist_account(entry, uid, game, nickname, enka_owner)
                except Exception as exc:
                    failed = True
                    self.client.capture_exception(exc)
                    embed, _ = _get_error_embed(exc, entry.interaction.locale)
                    with contextlib.suppress(discord.NotFound, discord.HTTPException):
                        if entry.interaction.message is not None:
                            await entry.interaction.followup.edit_message(
                                message_id=entry.interaction.message.id,
                                embed=embed,
                                view=None,
                            )

            if not failed:
                embed = _default_embed(
                    entry.interaction.locale,
                    title_key=finished_title,
                    desc_key=finished_desc,
                )
                with contextlib.suppress(discord.NotFound, discord.HTTPException):
                    if entry.interaction.message is not None:
                        await entry.interaction.followup.edit_message(
                            message_id=entry.interaction.message.id,
                            embed=embed,
                            view=None,
                        )

    # ------------------------------------------------------------------ #
    # Background task: poll entries                                       #
    # ------------------------------------------------------------------ #

    @tasks.loop(seconds=15)
    async def _check_entries(self) -> None:
        """Poll every active entry for expiry and verification conditions.

        The task runs every 15 seconds to catch TTL expiry quickly, but
        actual external API calls are rate-limited to once per
        ``_CHECK_INTERVAL_SECONDS`` per entry to avoid spam.
        """
        now = discord.utils.utcnow()
        for entry in self._linking_cache.copy():
            try:
                # Always check TTL — no cooldown needed here.
                if entry.started < now - datetime.timedelta(minutes=_ENTRY_TTL_MINUTES):
                    embed = _default_embed(
                        entry.interaction.locale,
                        title_key="linking.expired.title",
                        desc_key="linking.expired.description",
                    )
                    with contextlib.suppress(discord.NotFound, discord.HTTPException):
                        print(entry.interaction.message, "MESSAGE")
                        if entry.interaction.message is not None:
                            await entry.interaction.followup.edit_message(
                                message_id=entry.interaction.message.id,
                                embed=embed,
                                view=None
                            )
                    await self.remove_entry(entry)
                    continue

                # Rate-limit external API calls: skip until cooldown expires.
                if (
                    entry.last_checked is not None
                    and (now - entry.last_checked).total_seconds() < _CHECK_INTERVAL_SECONDS
                ):
                    continue

                entry.last_checked = now

                if entry.method == "UID":
                    await self._check_uid_entry(entry)
                elif entry.method == "Enka":
                    await self._check_enka_entry(entry)

            except Exception as exc:
                embed, recognized = _get_error_embed(exc, entry.interaction.locale)
                if not recognized:
                    self.client.capture_exception(exc)
                with contextlib.suppress(discord.NotFound, discord.HTTPException):
                    if entry.interaction.message is not None:
                        await entry.interaction.followup.edit_message(
                            message_id=entry.interaction.message.id,
                            embed=embed,
                            view=None,
                        )
                await self.remove_entry(entry)

    # ------------------------------------------------------------------ #
    # Internal: per-method check logic                                    #
    # ------------------------------------------------------------------ #

    async def _check_uid_entry(self, entry: LinkingEntryTemplate) -> None:
        """Check whether the user has placed the verification code in their in-game signature."""
        uid, game = entry.data[0]
        data = await self._fetch_enka(uid, game)

        nickname = self._extract_nested(data, NICKNAME_LOC[game])
        signature = self._extract_nested(data, SIGNATURE_LOC[game])

        if str(entry.code) not in signature:
            return  # Code not found yet — wait for next poll

        enka_owner: EnkaOwner | None = None
        if data.get("owner"):
            enka_owner = EnkaOwner(
                userhash=data["owner"]["hash"],
                username=data["owner"]["username"],
            )

        await self._persist_account(entry, uid, game, nickname, enka_owner)
        await self.remove_entry(entry)

        embed = _default_embed(
            entry.interaction.locale,
            title_key="linking.uid.success.title",
            desc_key="linking.uid.success.description",
        )
        with contextlib.suppress(discord.NotFound, discord.HTTPException):
            if entry.interaction.message is not None:
                await entry.interaction.followup.edit_message(
                    message_id=entry.interaction.message.id,
                    embed=embed,
                    view=None,
                )

    async def _check_enka_entry(self, entry: LinkingEntryTemplate) -> None:
        """Check whether the user has placed the verification code in their Enka profile bio."""
        assert entry.enka_username is not None

        # Invalidate cache so we always read fresh bio data.
        self._linking_client.invalidate_enka_profile_cache(entry.enka_username)
        data = await self._linking_client.fetch_enka_profile(entry.enka_username)
        bio: str = data.get("profile", {}).get("bio", "")
        if str(entry.code) not in bio:
            return  # Code not in bio yet — wait for next poll

        # Verification confirmed
        embed = _default_embed(
            entry.interaction.locale,
            title_key="linking.enka.verified.title",
            desc_key="linking.enka.verified.description",
        )
        with contextlib.suppress(discord.NotFound, discord.HTTPException):
            if entry.interaction.message is not None:
                await entry.interaction.followup.edit_message(
                    message_id=entry.interaction.message.id,
                    embed=embed,
                    view=None,
                )

        await self._queue.put(entry)
        await self.remove_entry(entry)


# ------------------------------------------------------------------ #
# Module-level helpers (lazy imports to avoid circular imports)       #
# ------------------------------------------------------------------ #

def _default_embed(
    locale: discord.Locale, *, title_key: str, desc_key: str
) -> discord.Embed:
    from zenox.embeds import DefaultEmbed
    from zenox.l10n import LocaleStr

    return DefaultEmbed(
        locale,
        title=LocaleStr(key=title_key),
        description=LocaleStr(key=desc_key),
    )


def _get_error_embed(
    error: Exception, locale: discord.Locale
) -> tuple[discord.Embed, bool]:
    from zenox.bot.error_handler import get_error_embed

    return get_error_embed(error, locale)
