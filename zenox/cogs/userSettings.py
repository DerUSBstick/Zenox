import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from typing import Any
from ..bot.bot import Zenox
from ..static.utils import ephemeral
from ..db.structures import UserConfig
from ..ui.user.view import UserSettingsUI

class UserSettings(commands.Cog):
    def __init__(self, client: Zenox) -> None:
        self.client = client
    
    @app_commands.command(
        name=locale_str("settings"),
        description=locale_str("Configure your user settings", key="settings_command_description")
    )
    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def settings_command(self, interaction: discord.Interaction) -> Any:
        await interaction.response.defer(ephemeral=ephemeral(interaction))

        settings = UserConfig(interaction.user.id).settings
        view = UserSettingsUI(
            author=interaction.user,
            locale=settings.language,
            settings=settings
        )
        await interaction.followup.send(
            embed=view.get_embed(),
            file=view.get_brand_image_file(),
            view=view
        )

        view.message = await interaction.original_response()

async def setup(client: Zenox) -> None:
    return
    # Do not add cog for now until there are features related to this
    await client.add_cog(UserSettings(client))