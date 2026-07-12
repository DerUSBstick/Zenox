import discord
from typing import TYPE_CHECKING, Any
from zenox.l10n import LocaleStr
from zenox.emojis import get_game_emoji
from zenox.db.classes import GameAccount
from ...components import Select, SelectOption, Button, ToggleButton

if TYPE_CHECKING:
    from ..view import AccountsView  # noqa: F401

class AccountSelector(Select["AccountsView"]):
    def __init__(self, accounts: list[GameAccount], selected: GameAccount) -> None:
        options = [
            SelectOption(
                label=f"{account.username} ({account.uid})",
                value=account.uid,
                emoji=get_game_emoji(account.game),
                default=account.uid == selected.uid
            ) for account in accounts
        ]
        super().__init__(options=options, placeholder=LocaleStr(key="account_select.placeholder"))
    
    async def callback(self, interaction: discord.Interaction) -> Any:
        selected_uid = self.values[0]
        self.view.selected = [account for account in self.view.user.accounts if account.uid == selected_uid][0]
        await self.view.refresh(interaction)

class PublicToggleButton(ToggleButton["AccountsView"]):
    def __init__(self, current_toggle: bool):
        super().__init__(
            current_toggle=current_toggle,
            toggle_label=LocaleStr(
                key="accounts.public_toggle.label"
            ),
        )
    
    async def callback(self, interaction: discord.Interaction) -> Any:
        assert self.view.selected is not None, "No account selected to toggle public/private."
        await super().callback(interaction)

        await self.view.selected._update_val("public", self.current_toggle)

        # Check if in the User Object the account is updated, get it via looping user.accounts
        acc = [account for account in self.view.user.accounts if account.uid == self.view.selected.uid][0]
        print(f"Account {acc.username} ({acc.uid}) public status updated to: {acc.public}")

class DeleteAccountButton(Button["AccountsView"]):
    def __init__(self) -> None:
        super().__init__(label=LocaleStr(key="account_delete_button.label"), style=discord.ButtonStyle.danger)
    
    async def callback(self, interaction: discord.Interaction) -> Any:
        assert self.view.selected is not None, "No account selected to delete."

        await self.view.user._remove_account(self.view.selected)
        self.view.selected = self.view.user.accounts[0] if self.view.user.accounts else None
        await self.view.refresh(interaction)