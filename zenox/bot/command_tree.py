import discord
import contextlib
from discord import InteractionType, NotFound, app_commands

from .error_handler import get_error_embed

class CommandTree(app_commands.CommandTree):
    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        error = error.original if isinstance(error, app_commands.errors.CommandInvokeError) else error

        if isinstance(error, app_commands.CheckFailure): # Test once without this return to see if capture_exception is working
            return
        
        embed, recognized = get_error_embed(error, discord.Locale.american_english)
        if not recognized:
            interaction.client.capture_exception(error)
        
        with contextlib.suppress(NotFound):
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)