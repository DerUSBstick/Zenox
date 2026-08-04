from __future__ import annotations

import discord

from typing import TYPE_CHECKING
from enum import StrEnum

from zenox import ui
from zenox.db.classes import UserConfig, GameAccount
from zenox.enums import Game
from zenox.emojis import get_game_emoji
from zenox.l10n import LocaleStr

from .containers import (
    AccountSettingsContainer,
    UserSettingsContainer,
    NoAccountsContainer,
)

if TYPE_CHECKING:
    from zenox.types import Interaction, User

class UserSettingsCategory(StrEnum):
    USER_SETTINGS = "user_settings"
    ACCOUNT_SETTINGS = "account_settings"

GAME_SELECT_CATEGORIES: set[UserSettingsCategory] = {
    UserSettingsCategory.ACCOUNT_SETTINGS,
}

class CategorySelector(ui.Select["UserSettingsView"]):
    def __init__(self, current_category: UserSettingsCategory) -> None:
        super().__init__(
            options=[
                ui.SelectOption(
                    label=LocaleStr(key=category.value),
                    value=category.value,
                    default=category == current_category,
                )
                for category in UserSettingsCategory
            ]
        )
    
    async def callback(self, i: Interaction) -> None:
        self.view.category = UserSettingsCategory(self.values[0])
        await self.view.update(i)

class AccountSelector(ui.Select["UserSettingsView"]):
    def __init__(self, accounts: list[GameAccount], selected: GameAccount | None, *, game_filter: Game | None = None) -> None:
        if accounts:
            options = [
                ui.SelectOption(
                    label=f"{account.username} ({account.uid})",
                    value=account.uid,
                    emoji=get_game_emoji(account.game),
                    default=selected is not None and account.uid == selected.uid
                ) for account in accounts if game_filter is None or account.game == game_filter
            ]
        else:
            options = [
                ui.SelectOption(
                    label=LocaleStr(key="account_select.no_accounts"),
                    value="no_accounts",
                    default=True,
                )
            ]
        super().__init__(options=options, placeholder=LocaleStr(key="account_select.placeholder"), disabled=not accounts)
    
    async def callback(self, interaction: Interaction) -> None:
        selected_uid = self.values[0]
        self.view.selected = [account for account in self.view.user.accounts if account.uid == selected_uid][0]

        await self.view.update(interaction)

class UserSettingsView(ui.LayoutView):
    def __init__(self, *, author: User, locale: discord.Locale, user: UserConfig):
        super().__init__(author=author, locale=locale)

        self.category = UserSettingsCategory.USER_SETTINGS

        self.user: UserConfig = user
        self.selected: GameAccount | None = user.accounts[0] if user.accounts else None
    
    async def _get_container(self) -> ui.Container:
        if self.category == UserSettingsCategory.USER_SETTINGS:
            return UserSettingsContainer(user=self.user)

        if self.category == UserSettingsCategory.ACCOUNT_SETTINGS:
            if self.user.accounts and self.selected is not None:
                return AccountSettingsContainer(user=self.user, selected=self.selected)
            return NoAccountsContainer()

        raise ValueError(f"Invalid category: {self.category}")

    async def update(self, i: Interaction) -> None:
        if not i.response.is_done():
            await i.response.defer()
        
        container = await self._get_container()
        container.add_item(discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))

        if self.category in GAME_SELECT_CATEGORIES:
            container.add_item(ui.ActionRow(AccountSelector(accounts=self.user.accounts, selected=self.selected)))
            container.add_item(discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small))
        
        container.add_item(ui.ActionRow(CategorySelector(current_category=self.category)))

        self.clear_items()
        self.add_item(container)

        self.message = await i.edit_original_response(view=self)