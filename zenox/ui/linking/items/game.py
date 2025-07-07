import discord
import random
from typing import TYPE_CHECKING, Any
from zenox.static.enums import Game
from zenox.static.constants import GAME_TO_EMOJI
from zenox.l10n import LocaleStr
from zenox.db.structures import LinkingEntryTemplate
from zenox.static.embeds import Embed
from ...components import Select, SelectOption, Modal, TextInput

if TYPE_CHECKING:
    from ..view import LinkingUI

class UIDInput(Modal):
    uid_input = TextInput(
                label=LocaleStr(key="linking_uid_input.label"),
                placeholder=LocaleStr(key="linking_uid_input.placeholder"),
                custom_id="uid_input",
                required=True,
                is_digit=True,
                min_length=9,
                max_length=10,
                style=discord.TextStyle.short,
            )
    def __init__(self) -> None:
        super().__init__(
            title=LocaleStr(key="linking_uid_input.title"),
            custom_id="linking:uid_input"
        )

class GameSelector(Select["LinkingUI"]):
    def __init__(self) -> None:
        options = self._get_options()
        super().__init__(options=options, placeholder=LocaleStr(key="game_select.placeholder"))

    @staticmethod
    def _get_options() -> list[SelectOption]:
        options: list[SelectOption] = []
        options.extend(
            [
                SelectOption(
                    label=game.name,
                    value=game.value,
                    emoji=GAME_TO_EMOJI[game]
                )
                for game in Game
            ]
        )
        return options

    async def callback(self, interaction: discord.Interaction) -> Any:
        selected = self.values[0]


        modal = UIDInput()
        modal.translate(self.view.locale)
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.incomplete:
            return
        
        uid = modal.uid_input.value
        
        await self.view.uid_linking(uid, Game(selected), interaction)