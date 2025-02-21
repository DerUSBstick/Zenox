import discord
from typing import TYPE_CHECKING, Any
from ...components import Select, SelectOption, ToggleButton
from zenox.l10n import LocaleStr
from zenox.static.constants import ZENOX_LOCALES

if TYPE_CHECKING:
    from ..view import UserSettingsUI

class LanguageSelector(Select["UserSettingsUI"]):
    def __init__(self, current_locale: discord.Locale | None) -> None:
        options = self._get_options(current_locale)
        super().__init__(options=options)
    
    @staticmethod
    def _get_options(current_locale: discord.Locale) -> list[SelectOption]:
        options: list[SelectOption] = []
        options.extend(
            [
                SelectOption(
                    label=ZENOX_LOCALES[locale]["name"],
                    value=locale.value,
                    emoji=ZENOX_LOCALES[locale]["emoji"],
                    default=locale.value == current_locale.value
                )
                for locale in ZENOX_LOCALES
            ]
        )
        return options
    
    async def callback(self, interaction: discord.Interaction) -> Any:
        selected = self.values[0]
        self.view.locale = discord.Locale(selected)
        self.view.settings.language = self.view.locale
        self.options = self._get_options(self.view.settings.language)
        self.update_options_defaults()
        await self.view.update_ui_and_save_settings(interaction, translate=True)

class DarkModeToggle(ToggleButton["UserSettingsUI"]):
    def __init__(self, current_toggle: bool) -> None:
        super().__init__(current_toggle, LocaleStr(key="dark_mode_button.label"))
    
    async def callback(self, interaction: discord.Interaction):
        await super().callback(interaction)
        self.view.settings.dark_mode = self.current_toggle
        await self.view.update_ui_and_save_settings(interaction)