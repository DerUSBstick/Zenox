import discord
import aiohttp
import os
from discord import Locale, Member, User
from typing import Literal
from zenox.l10n import LocaleStr
from zenox.bot.bot import Zenox

from ...static.enums import Game
from ...static.utils import parse_cookie, generate_hoyolab_token
from ...static.constants import GAME_TO_EMOJI, LINKING_IMAGE_GUIDE, HOYOLAB_GAME_ID_TO_GAME, SUPPORTED_LINKING_GAMES, HOYOLAB_LINKING_GUIDE
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
        self.methods: list[str] = ["UID", "Hoyolab"]
        self.method: Literal["UID", "Hoyolab"]
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
    
    async def hoyolab_linking(self, hoyolab_id: str, interaction: discord.Interaction[Zenox]) -> None:
        """Perfoms some Checks and starts the linking process for Hoyolab."""
        try:
            headers = {
                "x-rpc-language": "en-us",
                "x-rpc-lang": "en-us",
            }
            async with aiohttp.ClientSession(cookies=parse_cookie(os.getenv("HOYOLAB_COOKIES")), headers=headers) as session:
                response = await session.get(
                    f"https://bbs-api-os.hoyolab.com/game_record/card/wapi/getGameRecordCard?uid={hoyolab_id}"
                )
                data = await response.json()
                if data["retcode"] == 10001: # not logged in
                    await generate_hoyolab_token()
                    session.cookie_jar.update_cookies(parse_cookie(os.getenv("HOYOLAB_COOKIES")))
                    response = await session.get(
                        f"https://bbs-api-os.hoyolab.com/game_record/card/wapi/getGameRecordCard?uid={hoyolab_id}"
                    )
                    data = await response.json()
                if response.status != 200 or data["retcode"] != 0:
                    embed = DefaultEmbed(
                        locale=self.locale,
                        title=LocaleStr(key="hoyolab_linking_embed_title.error"),
                        description=LocaleStr(key="hoyolab_linking_embed_description.error")
                    )
                    await interaction.followup.edit_message(
                        message_id=interaction.message.id,
                        embed=embed,
                        view=None
                    )
                    raise Exception(f"Hoyolab API returned {response.status}")
                elif not data["data"]["list"] or all(account["game_id"] not in SUPPORTED_LINKING_GAMES for account in data["data"]["list"]):
                    embed = DefaultEmbed(
                        locale=self.locale,
                        title=LocaleStr(key="hoyolab_linking_embed_title.error"),
                        description=LocaleStr(key="hoyolab_linking_embed_description.no_accounts")
                    )
                    await interaction.followup.edit_message(
                        message_id=interaction.message.id,
                        embed=embed,
                        view=None
                    )
                    return
                already_linked: list[tuple[str, Game]] = []
                linked_someone_else: list[tuple[str, Game]] = []
                accounts: list[dict[str, Game]] = []
                for account in data["data"]["list"]:
                    if account["game_id"] not in SUPPORTED_LINKING_GAMES:
                        continue
                    is_linked = linking_cache.uid_is_already_linked(uid=account["game_role_id"], game=HOYOLAB_GAME_ID_TO_GAME[account["game_id"]], user_id=interaction.user.id)
                    if is_linked == 1:
                        linked_someone_else.append((account["game_role_id"], HOYOLAB_GAME_ID_TO_GAME[account["game_id"]]))
                        continue
                    elif is_linked == 2:
                        already_linked.append((account["game_role_id"], HOYOLAB_GAME_ID_TO_GAME[account["game_id"]]))
                        continue
                    game = HOYOLAB_GAME_ID_TO_GAME[account["game_id"]]
                    accounts.append((str(account["game_role_id"]), game))
                if rm:=linking_cache.is_uid_linking(accounts):
                    for account in rm:
                        accounts.remove(account)
                if not accounts:
                    embed = DefaultEmbed(
                        locale=self.locale,
                        title=LocaleStr(key="hoyolab_linking_embed_title.error"),
                        description=LocaleStr(key="hoyolab_linking_embed_description.already_linked")
                    )
                    if already_linked:
                        embed.add_field(
                            name=LocaleStr(key="hoyolab_linking_embed_field.already_linked"),
                            value="\n".join(
                                f"{GAME_TO_EMOJI[account[1]]} {account[0]}"
                                for account in already_linked
                            ),
                            inline=False
                        )
                    if linked_someone_else:
                        embed.add_field(
                            name=LocaleStr(key="hoyolab_linking_embed_field.linked_someone_else"),
                            value="\n".join(
                                f"{GAME_TO_EMOJI[account[1]]} {account[0]}"
                                for account in linked_someone_else
                            ),
                            inline=False
                        )
                    await interaction.followup.edit_message(
                        message_id=interaction.message.id,
                        embed=embed,
                        view=None
                    )
                    return
                entry = LinkingEntryTemplate(
                    method="Hoyolab",
                    hoyolab_id=hoyolab_id,
                    data=accounts,
                    user_id=interaction.user.id,
                    started=discord.utils.utcnow(),
                    code=18461, # Placeholder code
                    interaction=interaction
                )

                embed = DefaultEmbed(
                    locale=self.locale,
                    title=LocaleStr(key="hoyolab_linking_embed_title.started"),
                    description=LocaleStr(key="hoyolab_linking_embed_description.started")
                )
                embed.add_field(
                    name=LocaleStr(key="hoyolab_linking_embed_field.hoyolab_id"),
                    value=f"```\n{hoyolab_id}```",
                    inline=False
                )
                embed.add_field(
                    name=LocaleStr(key="hoyolab_linking_embed_field.code"),
                    value=f"```\n{entry.code}```",
                    inline=False
                )
                # List all accounts to be linked
                embed.add_field(
                    name=LocaleStr(key="hoyolab_linking_embed_field.accounts"),
                    value="\n".join(
                        f"{GAME_TO_EMOJI[account[1]]} {account[0]}"
                        for account in entry.data
                    ),
                    inline=False
                )
                embed.add_field(
                    name=LocaleStr(key="hoyolab_linking_embed_field.expires"),
                    value=f"<t:{int(entry.started.timestamp()) + 60 * 15}:R>",
                    inline=False
                )
                embed.add_field(
                    name=LocaleStr(key="hoyolab_linking_embed_field.how_to_complete"),
                    value=LocaleStr(key="hoyolab_linking_embed_description.how_to_complete"),
                    inline=False
                )
                embed.set_image(url=HOYOLAB_LINKING_GUIDE)
                embed.set_footer(text=LocaleStr(key="hoyolab_linking_embed_footer"))

                linking_cache.add_entry(entry)
                await interaction.followup.edit_message(
                    message_id=interaction.message.id,
                    embed=embed,
                    view=None
                )
                self.message = None
                    
        except Exception as e:
            interaction.client.capture_exception(e)

        

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