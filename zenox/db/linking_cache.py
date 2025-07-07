# # A class with a function checking every entry in the cache for various conditions
# from zenox.db.structures import LinkingEntryTemplate

import discord
import datetime
import requests
import asyncio
import aiohttp
import os
from discord.ext import tasks
from zenox.db.structures import LinkingEntryTemplate, UserConfig, GameAccountTemplate, DB, AccountOwner, HoyolabAccount
from zenox.l10n import LocaleStr
from zenox.static.embeds import DefaultEmbed
from zenox.static.enums import Game
from zenox.static.utils import generate_hoyolab_token, parse_cookie
from zenox.bot.error_handler import get_error_embed
from zenox.static.exceptions import HoyolabAPIError, EnkaAPIError

class LinkingCacheManager:
    REQUEST_URL = {
        Game.GENSHIN: "https://enka.network/api/uid/{uid}?info",
        Game.STARRAIL: "https://enka.network/api/hsr/uid/{uid}?info",
        Game.ZZZ: "https://enka.network/api/zzz/uid/{uid}?info",
    }
    SIGNATURE = {
        Game.GENSHIN: ["playerInfo", "signature"],
        Game.STARRAIL: ["detailInfo", "signature"],
        Game.ZZZ: ["PlayerInfo", "SocialDetail", "Desc"]
    }
    NICKNAME = {
        Game.GENSHIN: ["playerInfo", "nickname"],
        Game.STARRAIL: ["detailInfo", "nickname"],
        Game.ZZZ: ["PlayerInfo", "SocialDetail", "ProfileDetail", "Nickname"]
    }

    def __init__(self):
        self._linkingCache: list[LinkingEntryTemplate] = []
        self.queue: asyncio.Queue[LinkingEntryTemplate] = asyncio.Queue()
        self.finalize_entries.start()
        self.check_entries.start()

    @property
    def is_cache_full(self) -> bool:
        """Check if the linking cache is full."""
        return len(self._linkingCache) >= 75

    def is_user_linked(self, user_id: int) -> bool:
        """Check if a user has an active linking session."""
        return any(entry.user_id == user_id for entry in self._linkingCache)

    def uid_is_already_linked(self, uid: str, game: Game, user_id: int) -> int:
        """0 = Not linked; 1 = Linked to someone else; 2 = Linked to user"""
        doc = DB.accounts.find_one({"uid": uid, "game": game.value})
        if not doc:
            return 0
        if doc["user_id"] != user_id:
            return 1
        return 2
    
    def is_uid_linking(self, data: list[tuple[str, Game]]) -> list[tuple[str, Game]]:
        """Check if a list of UIDs are currently linking."""
        linking_uids = []
        entries = self.get_entries()
        for uid, game in data:
            for entry in entries:
                if any(uid == x and game == y for x, y in entry.data):
                    linking_uids.append((uid, game))
        return linking_uids
                

    def add_entry(self, entry: LinkingEntryTemplate) -> None:
        """Add a new entry to the linking cache."""
        self._linkingCache.append(entry)

    def get_entries(self) -> list[LinkingEntryTemplate]:
        """Get all entries in the linking cache."""
        return self._linkingCache.copy()

    def remove_entry(self, obj: LinkingEntryTemplate) -> None:
        """Remove an entry from the linking cache by the Object"""
        self._linkingCache.remove(obj)
    

    # Rework
    def check_uid(self, uid: str, game: Game, code: int) -> tuple[bool, str | None]:
        print(f"Checking UID: {uid} for game: {game}")
        """Verify a UID by checking it's signature for the code."""
        url = self.REQUEST_URL[game].format(uid=uid)
        try:
            response = requests.get(url, timeout=5)
            response_json = response.json()
            print(response.json(), response.status_code)
            if response.status_code != 200:
                return False, f"enka_response.{response.status_code}"
            
            # Get the signature from the response
            signature = response_json
            for key in self.SIGNATURE[game]:
                signature = signature[key]
                
            if str(code) in signature:
                return True, None

            return False, None
        except:
            return False, "check_uid_unknown_error"
    
    @tasks.loop(seconds=10)
    async def finalize_entries(self) -> None:
        """Finalize entries in the linking cache."""
        while not self.queue.empty():
            entry = await self.queue.get()
            if entry.method == "Hoyolab":
                for uid, game in entry.data:
                    async with aiohttp.ClientSession() as session:
                        url = self.REQUEST_URL[game].format(uid=uid)
                        try:
                            enka = None
                            response = await session.get(url, timeout=5)
                            response_json = await response.json()
                            if response.status != 200:
                                raise EnkaAPIError(status_code=response.status)
                            if "owner" in response_json and response_json["owner"]:
                                enka = AccountOwner(userhash=response_json["owner"]["hash"], username=response_json["owner"]["username"])
                            nickname = response_json
                            for key in self.NICKNAME[game]:
                                nickname = nickname[key]
                            hlb = HoyolabAccount(hoyolab_id=entry.hoyolab_id)
                            account = GameAccountTemplate(
                                uid=uid,
                                username=nickname,
                                game=game.value,
                                user_id=entry.user_id,
                                owner=enka,
                                hoyolab=hlb
                            )
                            user = UserConfig(userID=entry.user_id)
                            user.addAccount(account)
                        except Exception as e:
                            print(f"Error finalizing entry for {uid} in {game}: {e}")
                            pass
                embed = DefaultEmbed(
                    locale=entry.interaction.locale,
                    title=LocaleStr(key="hoyolab_linking_embed_title.finished"),
                    description=LocaleStr(key="hoyolab_linking_embed_description.finished")
                )
                try:
                    await entry.interaction.followup.edit_message(
                        message_id=entry.interaction.message.id,
                        embed=embed,
                        view=None
                    )
                except discord.NotFound:
                    pass

                            
            

    @tasks.loop(seconds=15)
    async def check_entries(self) -> None:
        """Check every entry in the cache for various conditions."""
        print("Checking entries in the linking cache...")
        for entry in self._linkingCache:
            try:
                if entry.started < discord.utils.utcnow() - datetime.timedelta(minutes=15):
                    # Remove the entry if it is older than 15 minutes
                    embed = DefaultEmbed(
                        locale=entry.interaction.locale,
                        title=LocaleStr(key="linking_embed_title.expired"),
                        description=LocaleStr(key="linking_embed_description.expired")
                    )
                    await entry.interaction.followup.edit_message(
                        message_id=entry.interaction.message.id,
                        embed=embed,
                        view=None
                    )
                    self.remove_entry(entry)
                elif entry.method == "Hoyolab":
                    headers = {
                        "accept": "application/json, text/plain, */*",
                        "accept-encoding": "gzip, deflate, br, zstd",
                        "accept-language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                        "content-type": "application/json",
                        "origin": "https://www.hoyolab.com",
                        "priority": "u=1, i",
                        "referer": "https://www.hoyolab.com/",
                        "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                        "sec-ch-ua-mobile": "?0",
                        "sec-ch-ua-platform": '"Windows"',
                        "sec-fetch-dest": "empty",
                        "sec-fetch-mode": "cors",
                        "sec-fetch-site": "same-site",
                        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                        "x-rpc-app_version": "3.10.0",
                        "x-rpc-client_type": "4",
                        "x-rpc-device_id": "3672d835-01ce-4a75-a65b-ea56abbfb3f8",
                        "x-rpc-hour": "18",
                        "x-rpc-language": "en-us",
                        "x-rpc-lrsag": "",
                        "x-rpc-page_info": '{"pageName":"","pageType":"","pageId":"","pageArrangement":"","gameId":""}',
                        "x-rpc-page_name": "",
                        "x-rpc-show-translated": "false",
                        "x-rpc-source_info": '{"sourceName":"","sourceType":"","sourceId":"","sourceArrangement":"","sourceGameId":""}',
                        "x-rpc-sys_version": "Windows NT 10.0",
                        "x-rpc-timezone": "Europe/Berlin",
                        "x-rpc-weekday": "7"
                    }
                    async with aiohttp.ClientSession(cookies=parse_cookie(os.getenv("HOYOLAB_COOKIES")), headers=headers) as session:
                        response = await session.post(
                            f"https://bbs-api-os.hoyolab.com/community/painter/wapi/user/full",
                            timeout=5,
                            json={"scene": 1, "uid": entry.hoyolab_id}
                        )
                        data = await response.json()
                        if data["retcode"] == 10001:
                            await generate_hoyolab_token()
                            session.cookie_jar.update_cookies(parse_cookie(os.getenv("HOYOLAB_COOKIES")))
                            response = await session.post(
                                f"https://bbs-api-os.hoyolab.com/community/painter/wapi/user/full",
                                timeout=5,
                                json={"uid": entry.hoyolab_id}
                            )
                            data = await response.json()
                        if response.status != 200 or data["retcode"] != 0:
                            raise HoyolabAPIError
                        if str(entry.code) in data["data"]["user_info"]["introduce"]:
                            embed = DefaultEmbed(
                                locale=entry.interaction.locale,
                                title=LocaleStr(key="hoyolab_linking_embed_title.success"),
                                description=LocaleStr(key="hoyolab_linking_embed_description.success")
                            )
                            await entry.interaction.followup.edit_message(
                                message_id=entry.interaction.message.id,
                                embed=embed,
                                view=None
                            )
                            await self.queue.put(entry)
                            self.remove_entry(entry)
                elif entry.method == "UID":
                    uid, game = entry.data[0]

                    url = self.REQUEST_URL[game].format(uid=uid)
                    async with aiohttp.ClientSession() as session:
                        response = await session.get(url, timeout=5)
                        response_json = await response.json()
                        if response.status != 200:
                            raise EnkaAPIError(status_code=response.status)
                        
                        nickname = response_json
                        for key in self.NICKNAME[game]:
                            nickname = nickname[key]
                        signature = response_json
                        for key in self.SIGNATURE[game]:
                            signature = signature[key]
                        if str(entry.code) in signature:
                            embed = DefaultEmbed(
                                locale=entry.interaction.locale,
                                title=LocaleStr(key="uid_linking_embed_title.success"),
                                description=LocaleStr(key="uid_linking_embed_description.success")
                            )
                            await entry.interaction.followup.edit_message(
                                message_id=entry.interaction.message.id,
                                embed=embed,
                                view=None
                            )
                            
                            # Don't need queue here
                            enka = None
                            hlb = HoyolabAccount(hoyolab_id=entry.hoyolab_id)
                            if "owner" in response_json and response_json["owner"]:
                                enka = AccountOwner(userhash=response_json["owner"]["hash"], username=response_json["owner"]["username"])
                            account = GameAccountTemplate(
                                uid=uid,
                                username=nickname,
                                game=game.value,
                                user_id=entry.user_id,
                                owner=enka,
                                hoyolab=hlb
                            )
                            user = UserConfig(userID=entry.user_id)
                            user.addAccount(account)
                            self.remove_entry(entry)
            except Exception as e:
                embed, recognized = get_error_embed(e, entry.interaction.locale)
                if not recognized:
                    entry.interaction.client.capture_exception(e)
                await entry.interaction.followup.edit_message(
                    message_id=entry.interaction.message.id,
                    embed=embed,
                    view=None
                )
                self.remove_entry(entry)

linking_cache = LinkingCacheManager()