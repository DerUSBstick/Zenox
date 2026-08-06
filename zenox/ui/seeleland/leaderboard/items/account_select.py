from __future__ import annotations

from typing import TYPE_CHECKING

from zenox import ui
from zenox.constants import Game
from zenox.l10n import LocaleStr

if TYPE_CHECKING:
    from zenox.db.classes import GameAccount
    from zenox.types import Interaction

    from ..view import SeelelandLeaderboardView


class AccountSelector(ui.Select["SeelelandLeaderboardView"]):
    def __init__(self, accounts: list[GameAccount], selected: GameAccount | None) -> None:
        starrail_accounts = [account for account in accounts if account.game == Game.STARRAIL]

        options = [
            ui.SelectOption(
                label=f"{account.username} ({account.uid})",
                value=account.uid,
                default=selected is not None and account.uid == selected.uid,
            )
            for account in starrail_accounts
        ]

        super().__init__(
            options=options,
            placeholder=LocaleStr(key="seeleland_lb.account_selector.placeholder"),
        )

    async def callback(self, interaction: Interaction) -> None:
        selected_uid = self.values[0]
        self.view.selected = next(
            account for account in self.view.user.accounts if account.uid == selected_uid
        )
        self.view.seele_data = await self.view.sl.get_player_data(self.view.selected.uid)
        self.view.selected_char_id = None
        self.view.selected_ctgr = None
        self.view.page = 1
        self.view.rankings = None

        await self.view.update(interaction)
