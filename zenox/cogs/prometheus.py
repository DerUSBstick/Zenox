from prometheus_client import start_http_server
from psutil import cpu_percent, virtual_memory
import time
from discord import Locale, Interaction, InteractionType
from discord.ext import commands, tasks
from zenox.bot.bot import Zenox
from zenox.metrics import *
from zenox.db.mongodb import DB
from zenox.db.structures import GuildConfig
from zenox.static.utils import get_now

class PrometheusCog(commands.Cog):
    port: int = 8000
    initial = False

    def __init__(self, client: Zenox):
        self.client = client

        if not self.latency_loop.is_running():
            self.latency_loop.start()
        if not self.system_usage_loop.is_running():
            self.system_usage_loop.start()
        if not self.update_locales.is_running():
            self.update_locales.start()
    
    @tasks.loop(seconds=5)
    async def latency_loop(self):
        for shard, latency in self.client.latencies:
            LATENCY_GAUGE.labels(shard).set(latency)
    
    @tasks.loop(seconds=5)
    async def system_usage_loop(self):
        RAM_USAGE_GAUGE.set(virtual_memory().percent)
        CPU_USAGE_GAUGE.set(cpu_percent())
        MEMORY_USAGE_GAUGE.set(virtual_memory().available * 100 / virtual_memory().total)

    @tasks.loop(minutes=30)
    async def update_locales(self):
        GUILD_LOCALE_GAUGE.clear()
        for guild in self.client.guilds:
            db_res = self.client.db.guilds.find_one({"id": guild.id}, {"language": 1})
            if db_res is None or db_res["language"] == "en-US":
                locale = guild.preferred_locale
            else:
                locale = Locale(db_res["language"])
            GUILD_LOCALE_GAUGE.labels(locale).inc()

    @commands.Cog.listener()
    async def on_ready(self):
        if self.initial:
            return
        self.initial = True

        GUILD_GAUGE.set(len(self.client.guilds))
        GUILD_MEMBER_GAUGE.set(sum(guild.member_count for guild in self.client.guilds))
        CHANNEL_GAUGE.set(sum(len(guild.text_channels) + len(guild.voice_channels) for guild in self.client.guilds))
        for guild in self.client.guilds:
            db_res = self.client.db.guilds.find_one({"id": guild.id}, {"language": 1})
            if db_res is None or db_res["language"] == "en-US":
                GUILD_LOCALE_GAUGE.labels(guild.preferred_locale).inc()
            else:
                GUILD_LOCALE_GAUGE.labels(Locale(db_res["language"])).inc()

        UPTIME_GAUGE.set(time.time())

        today = get_now().strftime("%Y-%m-%d")
        doc = DB.const.find_one({"_id": "commands_daily_total"}, {"usage": 1})
        if doc and "usage" in doc:
            for entry in doc["usage"]:
                if entry.get("date") == today:
                    COMMANDS_DAILY_TOTAL.labels(date=today).inc(entry.get("total", 0))
                    break

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
        GUILD_MEMBER_GAUGE.set(sum(guild.member_count for guild in self.client.guilds))
        CHANNEL_GAUGE.set(sum(len(guild.channels) for guild in self.client.guilds))

    @commands.Cog.listener()
    async def on_guild_remove(self, _):
        GUILD_GAUGE.set(len(self.client.guilds))
        GUILD_MEMBER_GAUGE.set(sum(guild.member_count for guild in self.client.guilds))
        CHANNEL_GAUGE.set(sum(len(guild.channels) for guild in self.client.guilds))

    @commands.Cog.listener()
    async def on_interaction(self, i: Interaction):
        if i.type == InteractionType.application_command:
            if i.command is not None:
                COMMANDS_DAILY_TOTAL.labels(date=get_now().strftime("%Y-%m-%d")).inc()
                today = get_now().strftime("%Y-%m-%d")
                command_name = i.command.name
                group = i.command.parent.name if i.command.parent else None

                update_query = {
                    "_id": "commands_daily_total",
                    "usage.date": today
                }
                cmd_path = f"{group}.{command_name}" if group else command_name
                update_op = {
                    "$inc": {f"usage.$.commands.{cmd_path}": 1, "usage.$.total": 1}
                }
                result = DB.const.update_one(update_query, update_op)

                if result.matched_count == 0:
                    commands_dict = {group: {command_name: 1}} if group else {command_name: 1}
                    DB.const.update_one(
                        {"_id": "commands_daily_total"},
                        {"$push": {"usage": {"date": today, "total": 1, "commands": commands_dict}}},
                        upsert=True
                    )

async def setup(client: Zenox):
    await client.add_cog(PrometheusCog(client))