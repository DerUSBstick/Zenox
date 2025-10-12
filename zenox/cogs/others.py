from __future__ import annotations

import discord
from discord import app_commands
from discord.app_commands import locale_str
import itertools
import psutil
from discord.ext import commands, tasks
from typing import TYPE_CHECKING
from ..embeds import DefaultEmbed
from ..l10n import LocaleStr

if TYPE_CHECKING:
    from ..bot import Zenox

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
    
    @app_commands.command(
        name=locale_str("about"),
        description=locale_str("Get information about the bot.", key="about_command")
    )
    async def about(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        locale = interaction.locale
        embed = DefaultEmbed(
            locale,
            title=f"{self.client.user.name if self.client.user else 'Zenox'} {self.client.version}",
            description=LocaleStr(key="about_command.desc", locale=locale),
        )

        # guild count
        embed.add_field(
            name=LocaleStr(key="about_command.guild_count"), value=str(len(interaction.client.guilds))
        )

        # ram usage
        embed.add_field(
            name=LocaleStr(key="about_command.ram_usage"), value=f"{self.client.ram_usage:.2f} MB"
        )

        # uptime
        uptime = discord.utils.format_dt(self.client.uptime, "R")
        embed.add_field(name=LocaleStr(key="about_command.uptime"), value=uptime)

        embed.set_image(url="https://cdn.alekeagle.me/62V2cKrg9m.png")

        await interaction.followup.send(embed=embed)

async def setup(client: Zenox) -> None:
    await client.add_cog(Others(client))