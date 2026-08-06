from __future__ import annotations

import re
from typing import TYPE_CHECKING

from zenox import ui
from zenox.clients.sl.constants import get_category_order
from zenox.clients.sl.formatting import format_category_label
from zenox.constants import SEELELAND_REGEX
from zenox.exceptions import SeelelandPageError
from zenox.l10n import LocaleStr

if TYPE_CHECKING:
    from zenox.types import Interaction

    from ..view import SeelelandLeaderboardView


class CategorySelector(ui.Select["SeelelandLeaderboardView"]):
    def __init__(self, view: SeelelandLeaderboardView) -> None:
        assert view.selected_char_id is not None
        assert view.seele_data is not None

        prefix = f"{view.selected_char_id}_"
        keys = [key for key in view.seele_data.leaderboard if key.startswith(prefix)]

        order = get_category_order(view.selected_char_id)

        def sort_key(key: str) -> int:
            match = re.match(SEELELAND_REGEX, key)
            team_code = match.group(4) if match else ""
            return order.index(team_code) if team_code in order else len(order)

        keys.sort(key=sort_key)

        if not keys:
            options = [
                ui.SelectOption(
                    label=LocaleStr(key="seeleland_lb.category_selector.no_categories"),
                    value="no_categories",
                )
            ]
        else:
            options = []
            for key in keys[:25]:
                score = view.seele_data.leaderboard[key]
                ctgr = key.removeprefix(prefix)
                options.append(
                    ui.SelectOption(
                        label=format_category_label(view.hsr, key, view.locale),
                        value=ctgr,
                        description=LocaleStr(
                            key="seeleland_lb.category_selector.description",
                            rank=score.rank,
                            percrank=score.percrank,
                        ),
                        default=ctgr == view.selected_ctgr,
                    )
                )

        super().__init__(
            options=options,
            placeholder=LocaleStr(key="seeleland_lb.category_selector.placeholder"),
            disabled=not keys,
        )

    async def callback(self, interaction: Interaction) -> None:
        assert self.view.selected_char_id is not None

        ctgr = self.values[0]
        self.view.selected_ctgr = ctgr
        self.view.page = 1

        try:
            self.view.rankings = await self.view.sl.get_rankings(self.view.selected_char_id, ctgr, 1)
        except SeelelandPageError:
            self.view.rankings = None

        await self.view.update(interaction)
