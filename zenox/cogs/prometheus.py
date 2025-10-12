from __future__ import annotations

import time
from discord.ext import commands, tasks
from prometheus_client import start_http_server
from psutil import cpu_percent, virtual_memory
from typing import TYPE_CHECKING, cast

from ..db.mongodb import DB

from ..metrics import CONNECTION_GAUGE, LATENCY_GAUGE, GUILD_GAUGE, GUILD_MEMBER_GAUGE, RAM_USAGE_GAUGE, CPU_USAGE_GAUGE, UPTIME_GAUGE, GUILD_LOCALE_GAUGE

if TYPE_CHECKING:
    from ..bot import Zenox

class PrometheusCog(commands.Cog):
    port: int = 8000
    initial: bool = False

    def __init__(self, client: Zenox):
        self.client = client

        if not self.update_gauges.is_running():
            self.update_gauges.start()
        if not self.system_usage_loop.is_running():
            self.system_usage_loop.start()
        if not self.latency_loop.is_running():
            self.latency_loop.start()

    @tasks.loop(minutes=30)
    async def update_gauges(self):
        GUILD_MEMBER_GAUGE.set(sum(guild.member_count or 0 for guild in self.client.guilds))
        await self.save_locales()

    @tasks.loop(seconds=5)
    async def system_usage_loop(self):
        RAM_USAGE_GAUGE.set(virtual_memory().percent)
        CPU_USAGE_GAUGE.set(cpu_percent())

    @tasks.loop(seconds=5)
    async def latency_loop(self):
        for shard, latency in self.client.latencies:
            LATENCY_GAUGE.labels(shard).set(latency)

    @commands.Cog.listener()
    async def on_ready(self):
        if self.initial:
            return
        self.initial = True
        
        GUILD_GAUGE.set(len(self.client.guilds))
        GUILD_MEMBER_GAUGE.set(sum(guild.member_count or 0 for guild in self.client.guilds))

        UPTIME_GAUGE.set(time.time())

        start_http_server(self.port)
    
    @commands.Cog.listener()
    async def on_connect(self):
        CONNECTION_GAUGE.labels(None).set(1)

    @commands.Cog.listener()
    async def on_resumed(self):
        CONNECTION_GAUGE.labels(None).set(1)

    @commands.Cog.listener()
    async def on_disconnect(self):
        CONNECTION_GAUGE.labels(None).set(0)

    @commands.Cog.listener()
    async def on_shard_ready(self, shard_id):
        CONNECTION_GAUGE.labels(shard_id).set(1)

    @commands.Cog.listener()
    async def on_shard_connect(self, shard_id):
        CONNECTION_GAUGE.labels(shard_id).set(1)

    @commands.Cog.listener()
    async def on_shard_resumed(self, shard_id):
        CONNECTION_GAUGE.labels(shard_id).set(1)

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard_id):
        CONNECTION_GAUGE.labels(shard_id).set(0)
    
    @commands.Cog.listener()
    async def on_guild_join(self, _):
        GUILD_GAUGE.set(len(self.client.guilds))

    @commands.Cog.listener()
    async def on_guild_remove(self, _):
        GUILD_GAUGE.set(len(self.client.guilds))

    async def save_locales(self):
        locales = [
            doc["language"]
            async for doc in DB.guilds.find()
            if "language" in doc
        ]
        locale_count = {locale: locales.count(locale) for locale in locales}
        for locale, count in locale_count.items():
            GUILD_LOCALE_GAUGE.labels(
                cast(str, locale).split("-")[-1].upper()
                if "-" in locale
                else cast(str, locale).upper()
            ).set(count)

async def setup(client: Zenox) -> None:
    await client.add_cog(PrometheusCog(client))