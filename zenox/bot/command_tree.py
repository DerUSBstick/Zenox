from __future__ import annotations

import discord
import contextlib
from typing import TYPE_CHECKING
from discord import app_commands

from .error_handler import get_error_embed

if TYPE_CHECKING:
    from ..types import Interaction


class CommandTree(app_commands.CommandTree):
    async def on_error(
        self,
        interaction: Interaction,
        e: app_commands.AppCommandError,
    ):
        error = (
            e.original if isinstance(e, app_commands.errors.CommandInvokeError) else e
        )

        if isinstance(error, app_commands.CheckFailure):
            return

        embed, recognized = get_error_embed(error, discord.Locale.american_english)
        if not recognized:
            interaction.client.capture_exception(error)

        with contextlib.suppress(discord.NotFound):
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
