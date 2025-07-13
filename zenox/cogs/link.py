import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from typing import Any
from zenox.db.mongodb import DB
from zenox.db.structures import GuildConfig, UserConfig
from zenox.l10n import LocaleStr
from zenox.static.embeds import DefaultEmbed
from ..bot.bot import Zenox
from zenox.ui.linking.view import LinkingUI
from zenox.db.linking_cache import linking_cache

class Link(commands.Cog):
    def __init__(self, client: Zenox) -> None:
        self.client = client

    @app_commands.command(
        name=locale_str("link"),
        description=locale_str("Link your accounts to the bot", key="link_command_description")
    )
    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=False)
    async def link_command(self, interaction: discord.Interaction) -> Any:
        await interaction.response.defer(ephemeral=True, thinking=True)
        if linking_cache.is_user_linked(interaction.user.id):
            await interaction.followup.send(
                content=locale_str("You already have an active linking session. Please complete it first or wait for it to expire.", key="linking_already_active")
            )
            return

        elif linking_cache.is_cache_full:
            await interaction.followup.send(
                content=locale_str("The linking queue is currently full. Please try again later.", key="linking_queue_full")
            )
            return

        view = LinkingUI(
            author=interaction.user,
            locale=interaction.locale
        )

        await view.start(interaction)
        view.message = await interaction.original_response()
    
async def setup(client: Zenox) -> None:
    await client.add_cog(Link(client))