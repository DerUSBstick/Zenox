from __future__ import annotations

from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from typing import TYPE_CHECKING

from zenox.ui.settings.users.view import UserSettingsView
from zenox.db.classes import UserConfig

if TYPE_CHECKING:
    from zenox.bot import Zenox
    from zenox.types import Interaction


class Settings(commands.Cog):
    def __init__(self, client: Zenox):
        self.client = client

    @app_commands.command(
        name=locale_str("settings"),
        description=locale_str(
            "Configure user settings", key="settings_command.description"
        ),
    )
    @app_commands.user_install()
    @app_commands.guild_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def settings_command(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)

        user = await UserConfig.new(interaction.user.id)
        view = UserSettingsView(
            author=interaction.user, locale=user.language, user=user
        )
        await view.update(interaction)


async def setup(client: Zenox) -> None:
    await client.add_cog(Settings(client))
