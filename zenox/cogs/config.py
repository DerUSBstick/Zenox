from __future__ import annotations

from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from typing import TYPE_CHECKING

from ..ui.guilds.view import GuildSettingsUI
from ..db.classes import Guild

if TYPE_CHECKING:
    from ..bot import Zenox
    from ..types import Interaction


class Config(commands.Cog):
    def __init__(self, client: Zenox):
        self.client = client

    @app_commands.command(
        name=locale_str("config"),
        description=locale_str(
            "Configure guild settings", key="config_command.description"
        ),
    )
    @app_commands.guild_install()
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.default_permissions(manage_guild=True)
    async def config_command(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)

        assert interaction.guild is not None

        guild = await Guild.new(interaction.guild.id)
        view = GuildSettingsUI(
            author=interaction.user, locale=guild.language, guild=guild
        )
        await interaction.followup.send(
            embed=view.get_embed(), file=view.get_brand_image_file(), view=view
        )

        view.message = await interaction.original_response()


async def setup(client: Zenox) -> None:
    await client.add_cog(Config(client))
