import datetime
from discord.ext import commands, tasks

from ..bot.bot import Zenox
from ..static.constants import UTC_8
from ..auto_tasks.cleanDB import cleanDB
from ..auto_tasks.topGG import TopGG
from ..auto_tasks.hoyolabCodes import hoyolabCodes
from ..auto_tasks.wikiCodes import wikiCodes
from ..auto_tasks.client_stats import client_stats

class Schedule(commands.Cog):
    def __init__(self, client: Zenox) -> None:
        self.client = client
    
    async def cog_load(self):
        if not self.client.config.schedule:
            return
        self.clean_db.start()
        self.request_hoyolab_codes.start()
        self.request_wiki_codes.start()
        self.publish_wiki_codes.start()
        self.update_topgg_count.start()
        self.update_client_stats.start()
    
    async def cog_unload(self):
        if not self.client.config.schedule:
            return
        self.clean_db.stop()
        self.request_hoyolab_codes.stop()
        self.request_wiki_codes.stop()
        self.publish_wiki_codes.stop()
        self.update_topgg_count.stop()
        self.update_client_stats.stop()
    
    @tasks.loop(time=datetime.time(0, 0, 0, tzinfo=UTC_8))
    async def clean_db(self):
        await cleanDB.execute(self.client)

    @tasks.loop(time=[datetime.time(hour, 0, 0, tzinfo=UTC_8) for hour in [1, 13]])
    async def request_wiki_codes(self):
        await wikiCodes.execute(self.client)
    
    @tasks.loop(time=[datetime.time(hour, 0, 0, tzinfo=UTC_8) for hour in [3, 15]])
    async def publish_wiki_codes(self):
        await wikiCodes.check_publish(self.client)

    @tasks.loop(minutes=3)
    async def request_hoyolab_codes(self):
        await hoyolabCodes.execute(self.client)

    @tasks.loop(time=datetime.time(0, 0, 0, tzinfo=UTC_8))
    async def update_topgg_count(self):
        await TopGG.execute(self.client)
    
    @tasks.loop(time=datetime.time(0, 0, 0, tzinfo=UTC_8))
    async def update_client_stats(self):
        await client_stats.execute(self.client)
    
    @clean_db.before_loop
    @request_hoyolab_codes.before_loop
    @request_wiki_codes.before_loop
    @publish_wiki_codes.before_loop
    @update_topgg_count.before_loop
    @update_client_stats.before_loop
    async def before_loops(self) -> None:
        await self.client.wait_until_ready()

async def setup(client: Zenox) -> None:
    await client.add_cog(Schedule(client))