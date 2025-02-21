import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from typing import Any
from ..bot.bot import Zenox
from ..static.utils import ephemeral
from ..db.structures import GuildConfig
from zenox.ui.guild.view import GuildSettingsUI

class GuildSettings(commands.Cog):
    def __init__(self, client: Zenox) -> None:
        self.client = client
    
    @app_commands.command(
        name=locale_str("config"),
        description=locale_str("Configure guild configuration", key="config_command_description")
    )
    @app_commands.guild_install()
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.default_permissions(manage_guild=True)
    async def config_command(self, interaction: discord.Interaction) -> Any:
        await interaction.response.defer(ephemeral=ephemeral(interaction))

        guildConfig = GuildConfig(interaction.guild.id)
        view = GuildSettingsUI(
            author=interaction.user,
            locale=guildConfig.language,
            settings=guildConfig
        )
        await interaction.followup.send(
            embed=view.get_embed(),
            file=view.get_brand_image_file(),
            view=view
        )

        view.message = await interaction.original_response()

async def setup(client: Zenox) -> None:
    await client.add_cog(GuildSettings(client))