from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from zenox import ui
from zenox.l10n import LocaleStr

from ..items import AccountSelector, CategorySelector, CharacterSelector

if TYPE_CHECKING:
    from ..view import SeelelandLeaderboardView


class FiltersContainer(ui.DefaultContainer["SeelelandLeaderboardView"]):
    def __init__(self, view: SeelelandLeaderboardView) -> None:
        children: list[ui.ActionRow | ui.TextDisplay | discord.ui.Separator] = [
            ui.TextDisplay(
                LocaleStr(
                    custom_str="# {title}",
                    title=LocaleStr(key="sl_command.description"),
                )
            ),
            discord.ui.Separator(visible=False, spacing=discord.SeparatorSpacing.small),
            ui.ActionRow(AccountSelector(view.user.accounts, view.selected)),
        ]

        if view.seele_data is not None:
            children.append(ui.ActionRow(CharacterSelector(view)))

        if view.selected_char_id is not None:
            children.append(ui.ActionRow(CategorySelector(view)))

        super().__init__(*children)
