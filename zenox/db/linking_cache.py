# # A class with a function checking every entry in the cache for various conditions
# from zenox.db.structures import LinkingEntryTemplate

import discord
import datetime
import requests
from discord.ext import tasks
from zenox.db.structures import LinkingEntryTemplate, UserConfig, GameAccountTemplate, DB
from zenox.l10n import LocaleStr
from zenox.static.embeds import DefaultEmbed
from zenox.static.enums import Game

class LinkingCacheManager:
    REQUEST_URL = {
        Game.GENSHIN: "https://enka.network/api/uid/{uid}",
        Game.STARRAIL: "https://enka.network/api/hsr/uid/{uid}",
        Game.ZZZ: "https://enka.network/api/zzz/uid/{uid}",
    }
    SIGNATURE = {
        Game.GENSHIN: ["playerInfo", "signature"],
        Game.STARRAIL: ["detailInfo", "signature"],
        Game.ZZZ: ["PlayerInfo", "SocialDetail", "Desc"]
    }

    def __init__(self):
        self._linkingCache: list[LinkingEntryTemplate] = []
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
        doc = DB.accounts.find_one({"uid": uid, "game": game.value, "user_id": user_id})
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

    @tasks.loop(seconds=15)
    async def check_entries(self) -> None:
        """Check every entry in the cache for various conditions."""
        print("Checking entries in the linking cache...")
        for entry in self._linkingCache:
            try:
                if entry.started < discord.utils.utcnow() - datetime.timedelta(minutes=2):
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
                elif entry.method == "UID":
                    # Unreachable UID check, because UID is not a method atm
                    url = self.REQUEST_URL[entry.data[0][1]].format(uid=entry.data[0][0])
                    try:
                        response = requests.get(url, timeout=5)
                        response_json = response.json()
                        if response.status_code != 200:
                            embed = DefaultEmbed(
                                locale=entry.interaction.locale,
                                title=LocaleStr(key="linking_embed_title.error"),
                                description=LocaleStr(key="linking_embed_description.error", error=f"enka_response.{response.status_code}")
                            )
                            await entry.interaction.followup.edit_message(
                                message_id=entry.interaction.message.id,
                                embed=embed,
                                view=None
                            )
                            self.remove_entry(entry)
                            continue

                        signature = response_json
                        for key in self.SIGNATURE[entry.data[0][1]]:
                            signature = signature[key]
                        print(f"Signature for UID {entry.data[0][0]}: {signature}")
                        if str(entry.code) in signature:
                            embed = DefaultEmbed(
                                locale=entry.interaction.locale,
                                title=LocaleStr(key="linking_embed_title.success"),
                                description=LocaleStr(key="linking_embed_description.success")
                            )
                            await entry.interaction.followup.edit_message(
                                message_id=entry.interaction.message.id,
                                embed=embed,
                                view=None
                            )
                            self.remove_entry(entry)
                            continue
                    except Exception as e:
                        print(f"Error checking UID {entry.data[0][0]}: {e}")
                        embed = DefaultEmbed(
                            locale=entry.interaction.locale,
                            title=LocaleStr(key="linking_embed_title.error"),
                            description=LocaleStr(key="check_uid_unknown_error")
                        )
                        await entry.interaction.followup.edit_message(
                            message_id=entry.interaction.message.id,
                            embed=embed,
                            view=None
                        )
                        self.remove_entry(entry)
                        continue
                print(f"Checking entry: {entry}")
            except Exception as e:
                ...

linking_cache = LinkingCacheManager()