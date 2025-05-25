import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import locale_str
from zenox.bot.bot import Zenox
from zenox.static.enums import Game
from zenox.ui.manual_codes.view import ManualCodesUI

class SendCodes(commands.Cog):
    def __init__(self, client: Zenox) -> None:
        self.client = client

    @app_commands.command(
        name="send_codes",
        description=locale_str("commands.send_codes.description")
    )
    @app_commands.describe(
        game=locale_str("commands.send_codes.game")
    )
    @app_commands.guild_install()
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app_commands.default_permissions(manage_guild=True)
    async def send_codes(self, interaction: discord.Interaction, game: Game):
        await interaction.response.defer(ephemeral=True)

        view = ManualCodesUI(
            author=interaction.user,
            locale=interaction.locale,
            game=game
        )
        await interaction.followup.send(
            embeds=view.get_embeds(),
            view=view
        )
        view.message = await interaction.original_response()
    
async def setup(client: Zenox) -> None:
    await client.add_cog(SendCodes(client))