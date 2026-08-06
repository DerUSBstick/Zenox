from __future__ import annotations

from typing import TYPE_CHECKING

from zenox import ui
from zenox.clients.sl.constants import SEELELAND_SITE_URL
from zenox.exceptions import SeelelandPageError
from zenox.l10n import LocaleStr

if TYPE_CHECKING:
    from zenox.types import Interaction

    from ..view import SeelelandLeaderboardView  # noqa: F401


class PrevPageButton(ui.Button["SeelelandLeaderboardView"]):
    def __init__(self, *, disabled: bool) -> None:
        super().__init__(
            label=LocaleStr(key="seeleland_lb.pagination.prev.label"),
            emoji="\u25c0\ufe0f",
            disabled=disabled,
        )

    async def callback(self, interaction: Interaction) -> None:
        view = self.view
        assert view.selected_char_id is not None
        assert view.selected_ctgr is not None

        view.page = max(1, view.page - 1)
        try:
            view.rankings = await view.sl.get_rankings(view.selected_char_id, view.selected_ctgr, view.page)
        except SeelelandPageError:
            view.rankings = None

        await view.update(interaction)


class NextPageButton(ui.Button["SeelelandLeaderboardView"]):
    def __init__(self, *, disabled: bool) -> None:
        super().__init__(
            label=LocaleStr(key="seeleland_lb.pagination.next.label"),
            emoji="\u25b6\ufe0f",
            disabled=disabled,
        )

    async def callback(self, interaction: Interaction) -> None:
        view = self.view
        assert view.selected_char_id is not None
        assert view.selected_ctgr is not None

        view.page = min(10, view.page + 1)
        try:
            view.rankings = await view.sl.get_rankings(view.selected_char_id, view.selected_ctgr, view.page)
        except SeelelandPageError:
            view.rankings = None

        await view.update(interaction)


class GoToLeaderboardButton(ui.Button["SeelelandLeaderboardView"]):
    def __init__(self, *, char_id: str, ctgr: str, page: int) -> None:
        url = f"{SEELELAND_SITE_URL.rstrip('/')}/leaderboards/lb/{char_id}/{ctgr}/{page}"
        super().__init__(
            label=LocaleStr(key="seeleland_lb.pagination.website.label"),
            url=url,
        )
