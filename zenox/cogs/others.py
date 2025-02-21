import discord
import pytz
import itertools
import psutil
from datetime import datetime
from discord.ext import commands, tasks

from ..bot.bot import Zenox

class Others(commands.Cog):
    def __init__(self, client: Zenox):
        self.client: Zenox = client
        self.process = psutil.Process()

    async def cog_load(self):
        if self.client.env != "prod":
            return
        self.update_vcs_state.start()
    
    async def cog_unload(self):
        if self.client.env != "prod":
            return
        self.update_vcs_state.cancel()
    
    @tasks.loop(hours=2)
    async def update_vcs_state(self):
        guild = self.client.get_guild(self.client.guild_id) or await self.client.fetch_guild(
            self.client.guild_id
        )

        CATEGORY_ID = 1337553668181856277
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        if category is None:
            return
        
        VC_IDS = [vc.id for vc in category.voice_channels]
        vc_rotator = itertools.cycle(VC_IDS)

        # Server Count
        server_count = len(self.client.guilds)
        vc = guild.get_channel(next(vc_rotator))
        if vc is not None:
            await vc.edit(name=f"{server_count} Servers")

    @update_vcs_state.before_loop
    async def before_loops(self) -> None:
        await self.client.wait_until_ready()

async def setup(client: Zenox) -> None:
    await client.add_cog(Others(client))