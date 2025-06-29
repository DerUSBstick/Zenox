# # A class with a function checking every entry in the cache for various conditions
# from zenox.db.structures import LinkingEntryTemplate

import discord
import datetime
from discord.ext import tasks
from zenox.db.structures import LinkingEntryTemplate
from zenox.l10n import LocaleStr
from zenox.static.embeds import DefaultEmbed

class LinkingCacheManager:
    def __init__(self):
        self._linkingCache: list[LinkingEntryTemplate] = []
        self.check_entries.start()

    @property
    def is_cache_full(self) -> bool:
        """Check if the linking cache is full."""
        return len(self._linkingCache) >= 100

    def is_user_linked(self, user_id: int) -> bool:
        """Check if a user has an active linking session."""
        return any(entry.user_id == user_id for entry in self._linkingCache)

    def add_entry(self, entry: LinkingEntryTemplate) -> None:
        """Add a new entry to the linking cache."""
        self._linkingCache.append(entry)

    def get_entries(self) -> list[LinkingEntryTemplate]:
        """Get all entries in the linking cache."""
        return self._linkingCache.copy()

    def remove_entry(self, obj: LinkingEntryTemplate) -> None:
        """Remove an entry from the linking cache by the Object"""
        self._linkingCache.remove(obj)

    # A method that checks every entry in the cache for various conditions every 5 seconds, using discord.tasks
    @tasks.loop(seconds=5)
    async def check_entries(self) -> None:
        """Check every entry in the cache for various conditions."""
        print("Checking entries in the linking cache...")
        for entry in self._linkingCache:
            if entry.started < discord.utils.utcnow() - datetime.timedelta(minutes=1):
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
                ...
            print(f"Checking entry: {entry}")

linking_cache = LinkingCacheManager()