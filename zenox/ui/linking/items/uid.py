import discord
from typing import TYPE_CHECKING, Any
from zenox.static.enums import Game
from zenox.l10n import LocaleStr
from ...components import Select, SelectOption, Modal, TextInput

if TYPE_CHECKING:
    from ..view import LinkingUI

class UIDInput(Modal["LinkingUI"]):
    uid_input = TextInput(
                label=LocaleStr(key="linking_uid_input.label"),
                placeholder=LocaleStr(key="linking_uid_input.placeholder"),
                custom_id="uid_input",
                required=True,
                min_length=9,
                max_length=10,
                style=discord.TextStyle.short,
            )
    def __init__(self) -> None:
        super().__init__(
            title=LocaleStr(key="linking_uid_input.title"),
            custom_id="linking:uid_input"
        )