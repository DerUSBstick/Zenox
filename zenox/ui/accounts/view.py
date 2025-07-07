import discord
import pathlib
from discord import Locale, User, Member
from zenox.db.structures import UserConfig, GameAccount
from zenox.static.embeds import DefaultEmbed
from zenox.static.constants import GAME_TO_EMOJI
from zenox.l10n import LocaleStr
from ..components import View
from .items.account import AccountSelector, DeleteAccountButton

class AccountsView(View):
    def __init__(
            self,
            *,
            author: User | Member,
            locale: Locale
    ):
        self.user = UserConfig(author.id)
        self.selected: GameAccount | None = self.user.accounts[0]
        super().__init__(author=author, locale=locale)
    
    def _add_items(self) -> None:
        self.add_item(AccountSelector(self.user.accounts, self.selected))
        self.add_item(DeleteAccountButton())

    def acc_embed(self) -> DefaultEmbed:
        # Returns an embed with the user's accounts
        if self.selected:
            embed = DefaultEmbed(
                locale=self.locale,
                title=self.selected.username + f" ({self.selected.uid})",
                description=LocaleStr(key="game", game=self.selected.game.value, emoji=GAME_TO_EMOJI[self.selected.game]),
            )
        else:
            embed = DefaultEmbed(
                locale=self.locale,
                title=LocaleStr(key="accounts_embed_title.no_accounts"),
                description=LocaleStr(key="accounts_embed_description.no_accounts")
            )
        return embed
    
    async def start(self, interaction: discord.Interaction) -> None:
        self._add_items()

        embed = self.acc_embed()
        
        
        self.message = await interaction.edit_original_response(
            embed=embed,
            view=self
        )
    
    async def refresh(self, interaction: discord.Interaction) -> None:
        embed = self.acc_embed()
        self.clear_items()
        if self.selected:
            self._add_items()
        await interaction.response.edit_message(
            embed=embed,
            view=self
        )