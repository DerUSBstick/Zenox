from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from zenox import emojis, ui
from zenox.db.classes import UserConfig, GameAccount
from zenox.l10n import LocaleStr

if TYPE_CHECKING:
    from zenox.types import Interaction

    from ..view import UserSettingsView # noqa: F401

class PublicToggleButton(ui.EmojiToggleButton["UserSettingsView"]):
    def __init__(self, current_toggle: bool):
        super().__init__(
            current=current_toggle,
        )
    
    async def callback(self, interaction: Interaction) -> None:
        assert self.view.selected is not None, "No account selected to toggle public/private."

        self.current = not self.current
        self.update_style()

        await self.view.selected._update_val("public", self.current)

        await self.view.update(interaction)

class DeleteAccountButton(ui.Button["UserSettingsView"]):
    def __init__(self) -> None:
        super().__init__(label=LocaleStr(key="account_delete_button.label"), style=discord.ButtonStyle.danger)
    
    async def callback(self, interaction: Interaction) -> None:
        assert self.view.selected is not None, "No account selected to delete."

        await self.view.user._remove_account(self.view.selected)
        self.view.selected = self.view.user.accounts[0] if self.view.user.accounts else None

        await self.view.update(interaction)

class AccountSettingsContainer(ui.DefaultContainer["UserSettingsView"]):
    def __init__(self, user: UserConfig, selected: GameAccount) -> None:
        super().__init__(
            ui.TextDisplay(
                LocaleStr(
                    custom_str="# {title}\n{description}",
                    title=LocaleStr(key="account_settings.title"),
                    description=LocaleStr(key="account_settings.description"),
                )
            ),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            ui.Section(
                ui.TextDisplay(
                    LocaleStr(
                        custom_str="### {emoji} {description}",
                        emoji=emojis.LANGUAGE,
                        description=LocaleStr(key="accounts.public_toggle.description"),
                    )
                ),
                accessory=PublicToggleButton(current_toggle=selected.public),
            ),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            ui.Section(
                ui.TextDisplay(
                    LocaleStr(
                        custom_str="### {emoji} {description}",
                        emoji=emojis.DELETE,
                        description=LocaleStr(key="accounts.delete_account.description"),
                    )
                ),
                accessory=DeleteAccountButton(),
            )
        )

class NoAccountsContainer(ui.DefaultContainer["UserSettingsView"]):
    def __init__(self) -> None:
        super().__init__(
            ui.TextDisplay(
                LocaleStr(
                    custom_str="# {title}\n{description}",
                    title=LocaleStr(key="account_settings.no_accounts.title"),
                    description=LocaleStr(key="account_settings.no_accounts.description"),
                )
            )
        )