from __future__ import annotations

import time
from discord.ext import commands, tasks
from prometheus_client import start_http_server
from psutil import cpu_percent, virtual_memory
from typing import TYPE_CHECKING, cast

from ..db.mongodb import DB
from ..db.classes import CacheEntry

from ..metrics import (
    CONNECTION_GAUGE, LATENCY_GAUGE, GUILD_GAUGE, GUILD_MEMBER_GAUGE, RAM_USAGE_GAUGE, CPU_USAGE_GAUGE,
    UPTIME_GAUGE, GUILD_LOCALE_GAUGE, CACHE_ENTRIES_GAUGE, CACHE_DB_DOCUMENTS_GAUGE,
    LINKING_ACTIVE_GAUGE, LINKING_QUEUE_GAUGE, SL_CHARACTER_INFO_GAUGE, LINKED_ACCOUNTS_GAUGE,
    flush_persistent_counters, load_persistent_counters, initialize_series,
)
from ..enums import Game
from ..clients.sl.leaderboards_catalog import SEELELAND_LEADERBOARDS_CATALOG
import discord

if TYPE_CHECKING:
    from ..bot import Zenox

class PrometheusCog(commands.Cog):
    port: int = 9180
    initial: bool = False

    def __init__(self, client: Zenox):
        self.client = client

        if not self.update_gauges.is_running():
            self.update_gauges.start()
        if not self.system_usage_loop.is_running():
            self.system_usage_loop.start()
        if not self.latency_loop.is_running():
            self.latency_loop.start()
        if not self.cache_stats_loop.is_running():
            self.cache_stats_loop.start()

    async def cog_unload(self) -> None:
        self.persist_metrics_loop.cancel()
        try:
            await flush_persistent_counters(DB.metrics)
        except Exception as exc:
            self.client.capture_exception(exc)

    @tasks.loop(seconds=60)
    async def persist_metrics_loop(self):
        try:
            await flush_persistent_counters(DB.metrics)
        except Exception as exc:
            self.client.capture_exception(exc)

    @tasks.loop(seconds=60)
    async def cache_stats_loop(self):
        try:
            CACHE_ENTRIES_GAUGE.set(len(CacheEntry.cache))
            CACHE_DB_DOCUMENTS_GAUGE.set(await DB.cache.estimated_document_count())
            counts = {game.value: 0 for game in Game}
            async for doc in await DB.accounts.aggregate([{"$group": {"_id": "$game", "n": {"$sum": 1}}}]):
                counts[str(doc["_id"])] = doc["n"]
            for game, count in counts.items():
                LINKED_ACCOUNTS_GAUGE.labels(game).set(count)
            linking = self.client.linking_cache
            if linking is not None:
                LINKING_ACTIVE_GAUGE.set(len(linking.get_entries()))
                LINKING_QUEUE_GAUGE.set(linking._queue.qsize())
        except Exception as exc:
            self.client.capture_exception(exc)

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

        initialize_series(SEELELAND_LEADERBOARDS_CATALOG, [game.value for game in Game])

        try:
            await load_persistent_counters(DB.metrics)
        except Exception as exc:
            self.client.capture_exception(exc)

        self.persist_metrics_loop.start()

        for char_id in SEELELAND_LEADERBOARDS_CATALOG:
            try:
                name = self.client.store.hsr.get_character_name(int(char_id), discord.Locale.american_english)
            except ValueError:
                name = None
            SL_CHARACTER_INFO_GAUGE.labels(char_id, name or char_id).set(1)

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