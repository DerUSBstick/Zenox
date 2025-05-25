# Button to add Codes and Select Menu to remove Code
import discord
from typing import TYPE_CHECKING
from zenox.ui.components import Button, Select, SelectOption, Modal, TextInput
from zenox.l10n import LocaleStr
from zenox.bot.bot import Zenox

if TYPE_CHECKING:
    from ..view import ManualCodesUI

class AddCodeButton(Button["ManualCodesUI"]):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.green,
            label=LocaleStr(key="manual_codes.add_code_button.label"),
            custom_id="add_code"
        )
    
    async def callback(self, interaction: discord.Interaction):
        ...

class RemoveCodeSelect(Select["ManualCodesUI"]):
    def __init__(self):
        options = self._get_options(self.view.codes)
        super().__init__(
            placeholder=LocaleStr(key="manual_codes.remove_code_select.placeholder"),
            custom_id="remove_code",
            min_values=1,
            max_values=1,
            options=options
        )
    
    @staticmethod
    def _get_options(codes: list[str]) -> list[SelectOption]:
        options: list[SelectOption] = []
        options.extend(
            [
                SelectOption(
                    label=code,
                    value=code
                )
                for code in codes
            ]
        )
        return options

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        self.view.codes.remove(selected)

        self.view.absolute_edit(interaction, embeds=self.view.get_embeds())
        