from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from zenox import emojis, ui
from zenox.db.classes import UserConfig
from zenox.constants import ZENOX_LOCALES
from zenox.l10n import LocaleStr

if TYPE_CHECKING:
    from zenox.types import Interaction

    from ..view import UserSettingsView # noqa: F401

class LanguageSelector(ui.Select["UserSettingsView"]):
    def __init__(self, current_locale: discord.Locale):
        options = self._get_options(current_locale)
        super().__init__(options=options)

    @staticmethod
    def _get_options(current_locale: discord.Locale) -> list[ui.SelectOption]:
        options: list[ui.SelectOption] = []
        options.extend(
            [
                ui.SelectOption(
                    label=ZENOX_LOCALES[locale]["name"],
                    value=locale.value,
                    emoji=ZENOX_LOCALES[locale]["emoji"],
                    default=locale == current_locale,
                )
                for locale in ZENOX_LOCALES
            ]
        )
        return options

    async def callback(self, i: Interaction) -> None:
        self.view.locale = discord.Locale(self.values[0])

        await self.view.user._update_language(self.view.locale)

        await self.view.update(i)

class UserSettingsContainer(ui.DefaultContainer["UserSettingsView"]):
    def __init__(self, user: UserConfig) -> None:
        super().__init__(
            ui.TextDisplay(
                LocaleStr(
                    custom_str="# {title}\n{description}",
                    title=LocaleStr(key="user_settings.title"),
                    description=LocaleStr(key="user_settings.description"),
                )
            ),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            ui.TextDisplay(
                LocaleStr(
                    custom_str="### {emoji} {description}",
                    emoji=emojis.LANGUAGE,
                    description=LocaleStr(key="user_settings.language_description"),
                )
            ),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            ui.ActionRow(LanguageSelector(current_locale=user.language)),
        )
