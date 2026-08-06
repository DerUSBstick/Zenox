from __future__ import annotations

from discord import Locale, User, Member
from typing import Any, TYPE_CHECKING
from zenox.constants import Game
from zenox.db.classes import UserConfig, GameAccount
from zenox.embeds import DefaultEmbed
from zenox.emojis import get_game_emoji
from zenox.l10n import LocaleStr
from zenox.clients.sl import SLClient, SeelelandResponse
from ..components import View, Select, SelectOption

from .items.filter import CharacterSelector

if TYPE_CHECKING:
    from zenox.types import Interaction

class SeeleView(View):
    def __init__(
            self,
            *,
            author: User | Member,
            user: UserConfig,
            locale: Locale
    ):
        self.user = user
        self.selected: GameAccount | None = self.user.accounts[0]
        self.seele_data: SeelelandResponse | None = None
        super().__init__(author=author, locale=locale)
    
    def _add_items(self) -> None:
        if self.selected:
            self.add_item(AccountSelector(self.user.accounts, self.selected, game_filter=Game.STARRAIL))

    def acc_embed(self) -> DefaultEmbed:
        # Returns an embed with the user's accounts
        if self.selected:
            embed = DefaultEmbed(
                locale=self.locale,
                title=self.selected.username + f" ({self.selected.uid})",
                description=LocaleStr(key="game", game=self.selected.game.value, emoji=get_game_emoji(self.selected.game)),
            )
        else:
            embed = DefaultEmbed(
                locale=self.locale,
                title=LocaleStr(key="accounts_embed_title.no_accounts"),
                description=LocaleStr(key="accounts_embed_description.no_accounts")
            )
        return embed
    
    async def start(self, interaction: Interaction) -> None:
        self.sl = SLClient(interaction.client)

        self._add_items()

        embed = self.acc_embed()
        
        
        self.message = await interaction.edit_original_response(
            embed=embed,
            view=self
        )
    
    async def refresh(self, interaction: Interaction) -> None:
        embed = self.acc_embed()
        self.clear_items()
        if self.selected:
            self._add_items()
        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

class AccountSelector(Select["SeeleView"]):
    def __init__(self, accounts: list[GameAccount], selected: GameAccount, *, game_filter: Game | None = None) -> None:
        options = [
            SelectOption(
                label=f"{account.username} ({account.uid})",
                value=account.uid,
                emoji=get_game_emoji(account.game),
                default=account.uid == selected.uid
            ) for account in accounts if game_filter is None or account.game == game_filter
        ]
        super().__init__(options=options, placeholder=LocaleStr(key="account_select.placeholder"))
    
    async def callback(self, interaction: Interaction) -> Any:
        selected_uid = self.values[0]
        self.view.selected = [account for account in self.view.user.accounts if account.uid == selected_uid][0]
        self.view.seele_data = await self.view.sl.get_player_data(self.view.selected.uid)

        self.view.clear_items()

        self.view.add_item(CharacterSelector(self.view, interaction.client.store.hsr))

        await interaction.response.edit_message(
            embed=self.view.acc_embed(),
            view=self.view
        )