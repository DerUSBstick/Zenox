import discord
from typing import TYPE_CHECKING, Any
from zenox.l10n import LocaleStr
from zenox.static.embeds import DefaultEmbed
from zenox.static.constants import GAME_TO_EMOJI
from zenox.db.structures import GameAccount
from ...components import Select, SelectOption, Button

if TYPE_CHECKING:
    from ..view import AccountsView

class AccountSelector(Select["AccountsView"]):
    def __init__(self, accounts: list[GameAccount], selected: GameAccount) -> None:
        options = [
            SelectOption(
                label=f"{account.username} ({account.uid})",
                value=account.uid,
                emoji=GAME_TO_EMOJI[account.game],
                default=account.uid == selected.uid
            ) for account in accounts
        ]
        super().__init__(options=options, placeholder=LocaleStr(key="account_select.placeholder"))
    
    async def callback(self, interaction: discord.Interaction) -> Any:
        selected_uid = self.values[0]
        self.view.selected = [account for account in self.view.user.accounts if account.uid == selected_uid][0]
        await self.view.refresh(interaction)

class DeleteAccountButton(Button["AccountsView"]):
    def __init__(self) -> None:
        super().__init__(label=LocaleStr(key="account_delete_button.label"), style=discord.ButtonStyle.danger)
    
    async def callback(self, interaction: discord.Interaction) -> Any:
        self.view.user.removeAccount(self.view.selected)
        self.view.selected = self.view.user.accounts[0] if self.view.user.accounts else None
        await self.view.refresh(interaction)