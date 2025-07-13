import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from zenox.bot.bot import Zenox
from zenox.commands.stats import StatsCommand

class Hoyo(commands.Cog):
    def __init__(self, client: Zenox):
        self.client = client
    
    @app_commands.command(
        name="stats", description=locale_str("View game account statistics", key="stats_command_description")
    )
    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=False)
    async def stats_command(self, interaction: discord.Interaction) -> None:
        command = StatsCommand(user=interaction.user)
        await command.run(interaction)


async def setup(client: Zenox) -> None:
        await client.add_cog(Hoyo(client))