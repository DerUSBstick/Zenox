import discord
from discord import Locale, Member, User
from typing import Literal
from zenox.l10n import LocaleStr

from ...static.enums import Game
from ...static.constants import GAME_TO_EMOJI, LINKING_IMAGE_GUIDE
from zenox.db.linking_cache import linking_cache
from ..components import View
from ...static.embeds import DefaultEmbed
from .items.method import MethodSelector
from zenox.db.structures import LinkingEntryTemplate

class LinkingUI(View):
    def __init(
            self,
            *,
            author: User | Member,
            locale: Locale
    ):
        super().__init__(author=author, locale=locale)
        self.methods: list[str] = ["UID"]
        self.method: Literal["UID"]
        self.game: Game
    
    def _add_items(self) -> None:
        self.add_item(MethodSelector())

    async def start(self, interaction: discord.Interaction) -> None:
        self._add_items()

        embed = DefaultEmbed(
            locale=self.locale,
            title=LocaleStr(key="linking_embed_title.method"),
            description=LocaleStr(key="linking_embed_description.method")
        )

        await interaction.followup.send(
            embed=embed,
            view=self
        )
    
    async def start_linking(self, entry: LinkingEntryTemplate) -> None:
        """Start the linking process for the given entry."""
        embed = DefaultEmbed(
            locale=self.locale,
            title=LocaleStr(key="linking_embed_title.started"),
            description=LocaleStr(key="linking_embed_description.started")
        )
        
        embed.add_field(
            name=LocaleStr(key="linking_embed_field.code"),
            value=f"```\n{entry.code}```",
            inline=False
        )
        
        if entry.method == "UID":
            # IF the method is UID, the list has only one UID
            embed.add_field(
                name=LocaleStr(key="linking_embed_field.uid"),
                value=GAME_TO_EMOJI[entry.game] + f" {entry.uid[0]}",
                inline=False
            )
        
        embed.add_field(
            # Expires in
            name=LocaleStr(key="linking_embed_field.expires"),
            # Value using discord t:TIME:R format
            value=f"<t:{int(entry.started.timestamp()) + 60 * 15}:R>",
            inline=False
        )

        # How to complete
        if entry.method == "UID":
            embed.add_field(
                name=LocaleStr(key="linking_embed_field.how_to_complete"),
                value=LocaleStr(key=f"linking_embed_description.how_to_complete"),
                inline=False
            )
            embed.set_image(
                url=LINKING_IMAGE_GUIDE[entry.game]
            )
        embed.set_footer(
            text=LocaleStr(key="linking_embed_footer")
        )
        linking_cache.add_entry(entry)
        await entry.interaction.followup.edit_message(
            message_id=entry.interaction.message.id,
            embed=embed,
            view=None
        )
        self.message = None