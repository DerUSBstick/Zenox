import discord
from discord import app_commands
from discord.app_commands import locale_str
from discord.ext import commands
from zenox.db.structures import UserConfig, GuildConfig
from zenox.db.mongodb import DB
from zenox.l10n import LocaleStr
from zenox.static.embeds import DefaultEmbed
from typing import Any
from ..bot.bot import Zenox
from zenox.ui.accounts.view import AccountsView

class Accounts(commands.Cog):
    def __init__(self, client: Zenox) -> None:
        self.client = client

    @app_commands.command(
        name=locale_str("accounts"),
        description=locale_str("Manage your accounts linked to the bot", key="accounts_command_description")
    )
    @app_commands.user_install()
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=False)
    async def accounts_command(self, interaction: discord.Interaction) -> Any:
        user = UserConfig(interaction.user.id)
        if not user.accounts:
            embed = DefaultEmbed(
                locale=interaction.locale,
                title=LocaleStr(key="accounts_embed_title.no_accounts"),
                description=LocaleStr(key="accounts_embed_description.no_accounts")
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        view = AccountsView(
            author=interaction.user,
            locale=interaction.locale
        )
        await view.start(interaction)

async def setup(client: Zenox) -> None:
    await client.add_cog(Accounts(client))