from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...components import Label, Modal, TextInput, Select, SelectOption
from zenox.l10n import LocaleStr
from zenox.enums import Game
from zenox.constants import LINKING_SUPPORTED_GAMES
from zenox.emojis import get_game_emoji

if TYPE_CHECKING:
    from zenox.types import Interaction
    from ..view import LinkingUI # noqa: F401

__all__ = ("GameSelector", "UIDModal")


class UIDModal(Modal):
    uid_input: Label[TextInput] = Label(
        text=LocaleStr(key="linking.uid_modal.uid.label"),
        component=TextInput(
            placeholder=LocaleStr(key="linking.uid_modal.uid.placeholder"),
            min_length=9,
            max_length=10,
        ),
    )

    def __init__(self) -> None:
        super().__init__(title=LocaleStr(key="linking.uid_modal.title"))


class GameSelector(Select["LinkingUI"]):
    def __init__(self) -> None:
        options = [
            SelectOption(
                label=game.value,
                value=game.value,
                emoji=get_game_emoji(game),
            )
            for game in LINKING_SUPPORTED_GAMES
        ]
        super().__init__(
            options=options,
            placeholder=LocaleStr(key="linking.game.placeholder"),
        )

    async def callback(self, interaction: Interaction) -> Any:
        game = Game(self.values[0])
        modal = UIDModal()
        modal.translate(self.view.locale)
        await interaction.response.send_modal(modal)
        await modal.wait()
        uid = modal.uid_input.component.value.strip()
        if not uid:
            return
        await self.view.uid_linking(uid, game, interaction)
