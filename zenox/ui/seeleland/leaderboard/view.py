from __future__ import annotations

from typing import TYPE_CHECKING

from zenox import ui
from zenox.clients.sl import SLClient
from zenox.constants import Game

from .containers import FiltersContainer, LeaderboardContainer, NoAccountContainer

if TYPE_CHECKING:
    import discord

    from zenox.bot import Zenox
    from zenox.clients.sl import RankingsResponse, SeelelandResponse
    from zenox.clients.store.hsr import HSRStore
    from zenox.db.classes import GameAccount, UserConfig
    from zenox.types import Interaction, User


class SeelelandLeaderboardView(ui.LayoutView):
    def __init__(self, *, author: User, locale: discord.Locale, user: UserConfig, client: Zenox) -> None:
        super().__init__(author=author, locale=locale)

        self.user: UserConfig = user
        self.sl = SLClient(client)
        self.hsr: HSRStore = client.store.hsr

        starrail_accounts = [account for account in user.accounts if account.game == Game.STARRAIL]
        self.selected: GameAccount | None = starrail_accounts[0] if starrail_accounts else None

        self.seele_data: SeelelandResponse | None = None
        self.selected_char_id: str | None = None
        self.selected_ctgr: str | None = None
        self.page: int = 1
        self.rankings: RankingsResponse | None = None

    async def update(self, i: Interaction) -> None:
        if not i.response.is_done():
            await i.response.defer()

        starrail_accounts = [account for account in self.user.accounts if account.game == Game.STARRAIL]

        if not starrail_accounts:
            self.clear_items()
            self.add_item(NoAccountContainer())
            self.message = await i.edit_original_response(view=self)
            return

        if self.selected is None:
            self.selected = starrail_accounts[0]

        if self.seele_data is None:
            self.seele_data = await self.sl.get_player_data(self.selected.uid)

        self.clear_items()
        self.add_item(FiltersContainer(self))

        if self.selected_ctgr is not None and self.rankings is not None:
            self.add_item(LeaderboardContainer(self))

        self.message = await i.edit_original_response(view=self)
