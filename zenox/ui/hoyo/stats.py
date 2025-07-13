from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from zenox.l10n import LocaleStr
from zenox.static.enums import Game
from zenox.static.constants import GAME_TO_EMOJI
from zenox.static.embeds import DefaultEmbed
from zenox.ui.components import View, Select, SelectOption
from zenox.db.structures import GameAccount

if TYPE_CHECKING:
    import genshin

class StatsView(View):
    def __init__(self, accounts: list[GameAccount], *, author: discord.User | discord.Member, locale: discord.Locale) -> None:
        super().__init__(author=author, locale=locale)
        self.accounts = accounts
        self.account = accounts[0]
        self.add_item(AccountSwitcher(accounts, self.account))
    
    def get_genshin_embed(self, genshin_user: genshin.models.PartialGenshinUserStats) -> DefaultEmbed:
        ...

    async def start(self, interaction: discord.Interaction) -> None:
        client = self.account.client
        
        if self.account.game is Game.GENSHIN:
            user = await client.get_partial_genshin_user(self.account.uid)


class AccountSwitcher(Select["StatsView"]):
    def __init__(self, accounts: list[GameAccount], account: GameAccount) -> None:
        super().__init__(
            placeholder=LocaleStr(key="account_select.placeholder"),
            options=[
                SelectOption(
                    label=account.blurred_uid,
                    value=f"{account.uid}:{account.game.value}",
                    emoji=GAME_TO_EMOJI[account.game],
                    default=account == account
                ) for account in accounts
            ]
        )
