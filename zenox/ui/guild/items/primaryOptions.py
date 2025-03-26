import discord
from typing import TYPE_CHECKING, Any
from zenox.l10n import LocaleStr
from zenox.static.constants import ZENOX_LOCALES, _supportCache as _cache, GAME_TO_EMOJI
from zenox.static.enums import Game
from ...components import Select, SelectOption, TextInput, Button, Modal
from zenox.static.utils import approve_request


if TYPE_CHECKING:
    from ..view import GuildSettingsUI

class LanguageSelector(Select["GuildSettingsUI"]):
    def __init__(self, current_locale: discord.Locale) -> None:
        options = self._get_options(current_locale)
        super().__init__(options=options)
    
    @staticmethod
    def _get_options(current_locale: discord.Locale) -> list[SelectOption]:
        options: list[SelectOption] = [
        ]
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
        self.view.settings.updateLanguage(self.view.locale)
        self.options = self._get_options(self.view.locale)
        self.update_options_defaults()
        await self.view.update_ui(interaction, translate=True)
    
class GameSelector(Select["GuildSettingsUI"]):
    def __init__(self) -> None:
        options = self._get_options()
        super().__init__(options=options, placeholder=LocaleStr(key="game_select.placeholder"))
    
    @staticmethod
    def _get_options() -> list[SelectOption]:
        options: list[SelectOption] = []
        options.extend(
            [
                SelectOption(
                    label=game,
                    value=game,
                    emoji=GAME_TO_EMOJI[game]
                )
                for game in Game
            ]
        )
        return options
    async def callback(self, interaction: discord.Interaction) -> Any:
        selected = self.values[0]
        await self.view.rebuild_ui(interaction, 'GameOptions', game=Game(selected))
        return

class PartnerMenu(Button["GuildSettingsUI"]):
    def __init__(self) -> None:
        super().__init__(
            label=LocaleStr(key="partner_menu.button.label"),
            style=discord.ButtonStyle.secondary,
            row=3
        )
    
    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.view.rebuild_ui(interaction, 'PartnerOptions')
        return

class SupportNumberModal(Modal):
    number_input = TextInput(label=LocaleStr(key="support_number_modal.number_input.label"), min_length=4, max_length=4, is_digit=True, min_value=1000, max_value=9999)
    note_input = TextInput(style=discord.TextStyle.long, label=LocaleStr(key="support_number_modal.note_input.label"), default=LocaleStr(key="support_number_modal.note_input.default"), required=False)

class SupportApprove(Button["GuildSettingsUI"]):
    def __init__(self) -> None:
        super().__init__(
            label=LocaleStr(key="support_approve.button.label"),
            style=discord.ButtonStyle.danger,
            row=3
        )
    
    async def callback(self, interaction):
        if str(interaction.guild.id) not in _cache:
            ALREADY_HANDLED = LocaleStr(key="support_approve.already_done").translate(self.view.settings.language)
            return await interaction.response.send_message(ALREADY_HANDLED, ephemeral=True)
        support_modal = SupportNumberModal(title=LocaleStr(key="support_number_modal.title"))
        support_modal.translate(self.view.settings.language)
        await interaction.response.send_modal(support_modal)
        await support_modal.wait()
        incomplete = support_modal.incomplete
        if incomplete:
            return
        await approve_request(interaction.guild.id, support_modal.number_input.value, interaction.client)

class SupportButton(Button["GuildSettingsUI"]):
    def __init__(self) -> None:
        super().__init__(
            label=LocaleStr(key="support_button.label"),
            style=discord.ButtonStyle.link,
            url="https://discord.gg/BsaUkhWs8T"
        )