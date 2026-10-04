from __future__ import annotations

from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from typing import TYPE_CHECKING

from ..db.classes import UserConfig
from ..embeds import ErrorEmbed
from ..l10n import LocaleStr
from ..ui.linking.view import LinkingUI

if TYPE_CHECKING:
    from ..bot import Zenox
    from ..types import Interaction


class Link(commands.Cog):
    def __init__(self, client: Zenox) -> None:
        self.client = client

    @app_commands.command(
        name=locale_str("link"),
        description=locale_str("Link your Game Accounts to your Discord Account", key="link_command.description"),
    )
    @app_commands.user_install()
    @app_commands.guild_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def link_command(self, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)

        cache = interaction.client.linking_cache
        if cache is None:
            return

        user = await UserConfig.new(interaction.user.id)

        if cache.is_user_linking(interaction.user.id):
            embed = ErrorEmbed(
                user.language,
                title=LocaleStr(key="linking.already_active.title"),
                description=LocaleStr(key="linking.already_active.description"),
            )
            await interaction.followup.send(embed=embed)
            return

        if cache.is_cache_full:
            embed = ErrorEmbed(
                user.language,
                title=LocaleStr(key="linking.cache_full.title"),
                description=LocaleStr(key="linking.cache_full.description"),
            )
            await interaction.followup.send(embed=embed)
            return

        view = LinkingUI(author=interaction.user, locale=user.language)
        await view.start(interaction)
        view.message = await interaction.original_response()


async def setup(client: Zenox) -> None:
    await client.add_cog(Link(client))