import discord
from typing import Any
from zenox.static.enums import Game
from zenox.l10n import LocaleStr
from ...components import Select, SelectOption, Modal, TextInput


class UIDInput(Modal):
    uid_input = TextInput(
                label=LocaleStr(key="linking_uid_input.label"),
                placeholder=LocaleStr(key="linking_uid_input.placeholder"),
                custom_id="uid_input",
                required=True,
                min_length=9,
                max_length=10,
                style=discord.TextStyle.short,
            )
    def __init__(self, *, min_length: int, max_length: int) -> None:
        super().__init__(
            title=LocaleStr(key="linking_uid_input.title"),
            custom_id="linking:uid_input"
        )
        if min_length:
            self.uid_input.min_length = min_length
        if max_length:
            self.uid_input.max_length = max_length