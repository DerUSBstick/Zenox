from __future__ import annotations

import time
import discord
from typing import TYPE_CHECKING, ClassVar

from zenox.embeds import DefaultEmbed
from zenox.db.mongodb import DB
from zenox.db.classes import Guild

if TYPE_CHECKING:
    from ..bot import Zenox


class CheckDatabase:
    _guilds: ClassVar[set[int]] = set()
    _db_guilds: ClassVar[set[int]] = set()
    _start: ClassVar[int] = 0
    _results: ClassVar[dict[str, int]] = {
        "skipped": 0,
        "restored": 0,
        "pending": 0,
        "deleted": 0,
        "error": 0,
    }

    @classmethod
    async def execute(cls, client: Zenox) -> None:
        cls._start = int(time.time())

        for guild in client.guilds:
            cls._guilds.add(guild.id)

        DB_GUILDS = DB.guilds.find({}, {"_id": 0, "id": 1})

        for guild in await DB_GUILDS.to_list():
            try:
                guild = await Guild.new(guild["id"])
                if guild.id in cls._guilds:  # Bot is in the guild
                    if guild.has_flag("PENDING_DELETION"):
                        await guild._update_flags("PENDING_DELETION", add=False)
                        cls._results["restored"] += 1
                        continue
                    cls._results["skipped"] += 1
                else:  # Bot is not in the guild
                    if guild.has_flag("PENDING_DELETION"):
                        await guild.delete()
                        cls._results["deleted"] += 1
                    else:
                        await guild._update_flags("PENDING_DELETION", add=True)
                        cls._results["pending"] += 1
            except Exception as e:
                cls._results["error"] += 1
                client.capture_exception(e)
        
        if client.webhook_url:
            webhook = discord.Webhook.from_url(client.webhook_url, client=client)
            embed = DefaultEmbed(
                locale=discord.Locale.american_english,
                title="Database Check Completed",
                description=(
                    f"**Skipped:** {cls._results['skipped']}\n"
                    f"**Restored:** {cls._results['restored']}\n"
                    f"**Pending Deletion:** {cls._results['pending']}\n"
                    f"**Deleted:** {cls._results['deleted']}\n"
                    f"**Errors:** {cls._results['error']}\n"
                ),
            )
            embed.set_footer(text=f"Time: {round(time.time() - cls._start, 3)} seconds")
            await webhook.send(embed=embed, username="Zenox Database Checker")
