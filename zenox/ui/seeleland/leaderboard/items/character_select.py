from __future__ import annotations

import re
from typing import TYPE_CHECKING

from zenox import ui
from zenox.constants import SEELELAND_REGEX
from zenox.l10n import LocaleStr

if TYPE_CHECKING:
    from zenox.types import Interaction

    from ..view import SeelelandLeaderboardView


class CharacterSelector(ui.Select["SeelelandLeaderboardView"]):
    def __init__(self, view: SeelelandLeaderboardView) -> None:
        char_ids: dict[str, None] = {}
        if view.seele_data is not None:
            for key in view.seele_data.leaderboard:
                match = re.match(SEELELAND_REGEX, key)
                if match is None:
                    continue
                char_id = match.group(1)
                if view.hsr.get_character(int(char_id)) is None:
                    continue
                char_ids.setdefault(char_id, None)

        if not char_ids:
            options = [
                ui.SelectOption(
                    label=LocaleStr(key="seeleland_lb.character_selector.no_characters"),
                    value="no_characters",
                    description=LocaleStr(key="seeleland_lb.character_selector.no_characters_description"),
                )
            ]
        else:
            options = [
                ui.SelectOption(
                    label=view.hsr.get_character_name(int(char_id), view.locale) or char_id,
                    value=char_id,
                    default=char_id == view.selected_char_id,
                )
                for char_id in list(char_ids)[:25]
            ]

        super().__init__(
            options=options,
            placeholder=LocaleStr(key="seeleland_lb.character_selector.placeholder"),
            disabled=not char_ids,
        )

    async def callback(self, interaction: Interaction) -> None:
        self.view.selected_char_id = self.values[0]
        self.view.selected_ctgr = None
        self.view.page = 1
        self.view.rankings = None

        await self.view.update(interaction)
