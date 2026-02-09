from __future__ import annotations

import datetime
from discord.ext import commands, tasks
from typing import TYPE_CHECKING
from zenox.constants import UTC_8

from ..auto_tasks.check_codes import CheckCodes
from ..auto_tasks.check_database import CheckDatabase
from ..auto_tasks.ytb_monitor import YTBMonitor

if TYPE_CHECKING:
    from zenox.bot.bot import Zenox

class Schedule(commands.Cog):
    def __init__(self, client: Zenox):
        self.client = client
    
    async def cog_load(self):
        if not self.client.config.schedule:
            return
        self.check_codes.start()
        self.check_database.start()
        self.ytb_monitor.start()
    
    async def cog_unload(self):
        if not self.client.config.schedule:
            return
        self.check_codes.stop()
        self.check_database.stop()
        self.ytb_monitor.stop()

    @tasks.loop(minutes=5)
    async def check_codes(self):
        await CheckCodes.execute(self.client)
    
    @tasks.loop(time=datetime.time(0, 0, 0, tzinfo=UTC_8))
    async def check_database(self):
        await CheckDatabase.execute(self.client)
    
    @tasks.loop(minutes=3)
    async def ytb_monitor(self):
        await YTBMonitor.execute(self.client)

    @check_codes.before_loop
    @check_database.before_loop
    @ytb_monitor.before_loop
    async def before_loops(self) -> None:
        await self.client.wait_until_ready()

async def setup(client: Zenox) -> None:
    await client.add_cog(Schedule(client))