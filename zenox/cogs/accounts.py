from __future__ import annotations

from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from typing import TYPE_CHECKING

from zenox.embeds import DefaultEmbed
from zenox.l10n import LocaleStr

from ..ui.accounts.view import AccountsView
from ..db.classes import UserConfig

if TYPE_CHECKING:
    from ..bot import Zenox
    from ..types import Interaction

class Accounts(commands.Cog):
    def __init__(self, client: Zenox) -> None:
        self.client = client

    @app_commands.command(
        name=locale_str("accounts"),
        description=locale_str("Manage your accounts linked to the bot", key="accounts_command_description")
    )
    @app_commands.user_install()
    @app_commands.guild_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def accounts_command(self, interaction: Interaction):
        user = await UserConfig.new(interaction.user.id)
        if not user.accounts:
            embed = DefaultEmbed(
                locale=user.language,
                title=LocaleStr(key="accounts_embed_title.no_accounts"),
                description=LocaleStr(key="accounts_embed_description.no_accounts")
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        view = AccountsView(
            author=interaction.user,
            locale=user.language,
            user=user
        )
        await view.start(interaction)

async def setup(client: Zenox) -> None:
    await client.add_cog(Accounts(client))