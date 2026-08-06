from __future__ import annotations

import re
from typing import TYPE_CHECKING
from zenox.l10n import LocaleStr
from zenox.constants import Game, SEELELAND_REGEX
from ...components import Select, SelectOption

if TYPE_CHECKING:
    from zenox.clients.store.hsr import HSRStore
    from ..view import SeeleView  # noqa: F401

class CharacterSelector(Select["SeeleView"]):
    def __init__(self, view: SeeleView, hsr: HSRStore) -> None:
        if not view.seele_data:
            options = [
                SelectOption(
                    label=LocaleStr(key="seele.character_selector.no_characters"),
                    value="no_characters",
                    description=LocaleStr(key="seele.character_selector.no_characters_description"),
                )
            ]
        else:
            characters = hsr.characters
            # Apply regex to char and take [0] to get the character ID
            char_ids = list(
                {match.group(1): (match.group(1), char) 
                for char in view.seele_data.leaderboard.keys() 
                if (match := re.match(SEELELAND_REGEX, char)) is not None and int(match.group(1)) in characters
                }.values()
            )

            # Options created dynamically based on the characters available for the selected account
            options: list[SelectOption] = []
            options.extend(
                [
                    SelectOption(
                        label=hsr.get_character_name(int(char_id), view.locale) or char_id,
                        value=char_id,
                        description=LocaleStr(key="seele.character_selector.description", game=Game.STARRAIL.value,)
                    ) for char_id, char in char_ids[:25]
                ]
            )
        super().__init__(
            options=options,
            placeholder=LocaleStr(key="seele.character_selector.placeholder"),
        )
