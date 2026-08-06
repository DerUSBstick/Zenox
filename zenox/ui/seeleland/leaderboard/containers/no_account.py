from __future__ import annotations

from typing import TYPE_CHECKING

from zenox import ui
from zenox.l10n import LocaleStr

if TYPE_CHECKING:
    from ..view import SeelelandLeaderboardView  # noqa: F401


class NoAccountContainer(ui.DefaultContainer["SeelelandLeaderboardView"]):
    def __init__(self) -> None:
        super().__init__(
            ui.TextDisplay(
                LocaleStr(
                    custom_str="# {title}\n{description}",
                    title=LocaleStr(key="seeleland_lb.no_account.title"),
                    description=LocaleStr(key="seeleland_lb.no_account.description"),
                )
            )
        )
