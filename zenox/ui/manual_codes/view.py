import discord
from discord import User, Member
from ..components import View, Button, Modal, TextInput, GoBackButton
from zenox.static.enums import Game
from zenox.static.constants import HOYO_REDEEM_URLS, GAME_THUMBNAILS
from zenox.static.embeds import Embed
from zenox.l10n import LocaleStr
from zenox.static import emojis
from zenox.static.utils import get_emoji

from .items.codes import AddCodeButton, RemoveCodeSelect

class ManualCodesUI(View):
    def __init__(
            self,
            *,
            author: User | Member,
            locale: discord.Locale,
            game: Game
    ):
        super().__init__(author=author, locale=locale)

        self.step: str = "start"
        self.game: Game = game
        self.codes: list[str] = []
        self.rewards: list[str, str] = []

        self.add_item(AddCodeButton())
        self.add_item(RemoveCodeSelect())
    
    def codes_embed(self) -> Embed:
        if not self.codes or not self.rewards:
            return None
        DIRECT_LINK = LocaleStr(key="direct_link").translate(self.locale)
        REWARDS = LocaleStr(key="rewards").translate(self.locale)

        DESC = f"\n{emojis.CODES1}{emojis.CODES2}{emojis.CODES3}\n"
        for code in self.codes:
            DESC += f"> {code} | **[{DIRECT_LINK}]({HOYO_REDEEM_URLS[self.game]+code})**\n"
        
        if self.rewards:
            DESC += f"\n**〓 {REWARDS} 〓**\n"
            for reward in self.rewards:
                DESC += f"{get_emoji(reward[0])} **{reward[0]} ×{reward[1]}**\n"

        return Embed(
            locale=self.locale,
            title=LocaleStr(key="wikicodes_embed.title"),
            description=DESC
            )

    def settings_embed(self) -> Embed:
        if self.step == "start":
            return Embed(
                locale=self.locale,
                title=LocaleStr(key="manual_codes_embed.start.title"),
                description=LocaleStr(key="manual_codes_embed.start.description")
            )

    def get_embeds(self) -> list[Embed]:
        embeds = [self.codes_embed(), self.settings_embed()]
        return embeds
