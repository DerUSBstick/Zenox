from __future__ import annotations

from typing import TYPE_CHECKING

from zenox import ui
from zenox.clients.sl.constants import SEELELAND_SITE_URL
from zenox.exceptions import SeelelandPageError
from zenox.l10n import LocaleStr

if TYPE_CHECKING:
    from zenox.types import Interaction

    from .view import SeelelandClassicPaginatorView  # noqa: F401


class FirstPageButton(ui.Button["SeelelandClassicPaginatorView"]):
    def __init__(self, *, disabled: bool) -> None:
        super().__init__(emoji="\u23ee\ufe0f", disabled=disabled, row=0)

    async def callback(self, interaction: Interaction) -> None:
        view = self.view
        view.page = 1
        try:
            view.rankings = await view.sl.get_rankings(
                view.char_id, view.ctgr, view.page, requested_by=interaction.user.id
            )
        except SeelelandPageError:
            pass

        await view.refresh(interaction)


class PrevPageButton(ui.Button["SeelelandClassicPaginatorView"]):
    def __init__(self, *, disabled: bool) -> None:
        super().__init__(
            label=LocaleStr(key="seeleland_lb.pagination.prev.label"),
            emoji="\u25c0\ufe0f",
            disabled=disabled,
            row=0,
        )

    async def callback(self, interaction: Interaction) -> None:
        view = self.view
        view.page = max(1, view.page - 1)
        try:
            view.rankings = await view.sl.get_rankings(
                view.char_id, view.ctgr, view.page, requested_by=interaction.user.id
            )
        except SeelelandPageError:
            pass

        await view.refresh(interaction)


class NextPageButton(ui.Button["SeelelandClassicPaginatorView"]):
    def __init__(self, *, disabled: bool) -> None:
        super().__init__(
            label=LocaleStr(key="seeleland_lb.pagination.next.label"),
            emoji="\u25b6\ufe0f",
            disabled=disabled,
            row=0,
        )

    async def callback(self, interaction: Interaction) -> None:
        view = self.view
        view.page = min(10, view.page + 1)
        try:
            view.rankings = await view.sl.get_rankings(
                view.char_id, view.ctgr, view.page, requested_by=interaction.user.id
            )
        except SeelelandPageError:
            pass

        await view.refresh(interaction)


class LastPageButton(ui.Button["SeelelandClassicPaginatorView"]):
    def __init__(self, *, disabled: bool) -> None:
        super().__init__(emoji="\u23ed\ufe0f", disabled=disabled, row=0)

    async def callback(self, interaction: Interaction) -> None:
        view = self.view
        view.page = 10
        try:
            view.rankings = await view.sl.get_rankings(
                view.char_id, view.ctgr, view.page, requested_by=interaction.user.id
            )
        except SeelelandPageError:
            pass

        await view.refresh(interaction)


class ShowLeaderboardDetailsButton(ui.Button["SeelelandClassicPaginatorView"]):
    def __init__(self) -> None:
        super().__init__(label=LocaleStr(key="seeleland_lb.classic.details_button.label"), row=1)

    async def callback(self, interaction: Interaction) -> None:
        embed = self.view.build_details_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)


class GoToLeaderboardButton(ui.Button["SeelelandClassicPaginatorView"]):
    def __init__(self, *, char_id: str, ctgr: str, page: int) -> None:
        url = f"{SEELELAND_SITE_URL.rstrip('/')}/leaderboards/lb/{char_id}/{ctgr}/{page}"
        super().__init__(
            label=LocaleStr(key="seeleland_lb.pagination.website.label"),
            url=url,
            row=1,
        )

