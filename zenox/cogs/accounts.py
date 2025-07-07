import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from typing import Any
from ..bot.bot import Zenox

class Accounts(commands.Cog):
    def __init__(self, client: Zenox) -> None:
        self.client = client

    @app_commands.command(
        name=locale_str("accounts"),
        description=locale_str("Manage your accounts linked to the bot", key="accounts_command_description")
    )
    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=False, dms=True, private_channels=False)
    async def accounts_command(self, interaction: discord.Interaction) -> Any:
        await interaction.response.defer(ephemeral=True, thinking=True)

async def setup(client: Zenox) -> None:
    await client.add_cog(Accounts(client))