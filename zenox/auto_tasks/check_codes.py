from __future__ import annotations

import asyncio
import time
import aiohttp
from typing import TYPE_CHECKING, ClassVar, TypedDict
import discord
from fake_useragent import UserAgent

from zenox import emojis
from zenox.constants import CODE_URLS, ZENOX_LOCALES, HOYO_REDEEM_URLS, GAME_THUMBNAILS, GAME_VALUABLES
from zenox.db.mongodb import DB
from zenox.enums import Game
from zenox.embeds import Embed
from zenox.db.classes import Guild, RedemptionCode
from zenox.ui.components import View, Button
from zenox.l10n import LocaleStr

if TYPE_CHECKING:
    from ..bot import Zenox

# interface or detailed response for _get_codes
class CodeData(TypedDict):
    code: str
    game: str
    status: str
    rewards: str

class CodeFetchResult(TypedDict):
    codes: list[CodeData]
    game: str

class CheckCodes:
    _client: ClassVar[Zenox]
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _ua = UserAgent()

    @classmethod
    async def _get_codes(cls, session: aiohttp.ClientSession, game: Game) -> CodeFetchResult:
        async with session.get(CODE_URLS[game], headers={"User-Agent": cls._ua.random}) as response:
            response.raise_for_status()
            codes = await response.json()
            return codes

    @classmethod
    async def execute(cls, client: Zenox) -> None:
        if cls._lock.locked():
            print("CheckCodes is already running, skipping this execution.")
            return
        
        if client.session is None:
            return
        
        assert client.db_config is not None, "Bot configuration is not loaded yet."

        async with cls._lock:
            cls._client = client
            for game in CODE_URLS.keys():
                if 0 < client.db_config.stream_codes_config[game].stream_time - int(time.time()) < 3600 and client.db_config.stream_codes_config[game].state != 5:
                    print(f"Stream for {game.value} is starting in less than 60 minutes and codes are not published yet, skipping code check for this game.")
                    continue
                try:
                    codes = await cls._get_codes(client.session, game)
                    published_codes: list[dict[str, str]] = []
                    for code_data in codes["codes"]:
                        if code_data["status"] != "OK":
                            continue
                        redemption_code = await RedemptionCode.new(code=code_data["code"], game=game)

                        if not redemption_code.published:
                            published_codes.append({"code": code_data["code"], "rewards": code_data["rewards"]})
                            redemption_code.published = True
                            await DB.codes.update_one({"code": redemption_code.code, "game": redemption_code.game.value}, {"$set": {"published": True}})
                    
                    if published_codes:
                        await cls.notify_codes(game, published_codes)
                    print(f"Published codes for {game.name}: {published_codes}")
                except Exception as e:
                    client.capture_exception(e)

    @classmethod
    def _pre_translate(cls, codes: list[dict[str, str]], game: Game) -> tuple[dict[discord.Locale, dict[str, str]], dict[discord.Locale, Embed], View]:
        VIEW_POPULATED: bool = False

        _translations: dict[discord.Locale, dict[str, str]] = {}
        _embeds: dict[discord.Locale, Embed] = {}
        _view = View(author=None, locale=discord.Locale.american_english) # Locale doesn't matter here

        for language in ZENOX_LOCALES:

            MESSAGE_CONTENT = LocaleStr(key="codes_notification.content", game_name=game.value).translate(language)
            EMBED_TITLE = LocaleStr(key="codes_notification.embed.title").translate(language)
            DIRECT_LINK = LocaleStr(key="codes_notification.direct_link").translate(language)

            DESC = f"\n{emojis.CODES1}{emojis.CODES2}{emojis.CODES3}\n"

            for code in codes:
                has_valuable = GAME_VALUABLES[game].lower() in code["rewards"].lower()
                DESC += f"> {emojis.GAME_VALUABLE_EMOJIS[game] if has_valuable else ''} `{code['code']}` | **[{DIRECT_LINK}]({HOYO_REDEEM_URLS[game]+code['code']})**\n"
                if not VIEW_POPULATED:
                    _view.add_item(Button(label=code["code"], url=HOYO_REDEEM_URLS[game]+code["code"], emoji=emojis.GAME_VALUABLE_EMOJIS[game] if has_valuable else None))
            
            VIEW_POPULATED = True
            
            embed = Embed(locale=language, title=EMBED_TITLE, description=DESC)
            embed.set_thumbnail(url=GAME_THUMBNAILS[game])

            _translations[language] = {"content": MESSAGE_CONTENT}
            _embeds[language] = embed
        
        return _translations, _embeds, _view

    @classmethod
    async def notify_codes(cls, game: Game, codes: list[dict[str, str]]) -> None:
        """Notifies guilds about new codes for a specific game."""
        print("Notifying guilds about new codes for", game.name, "Codes:", codes)
        notifies = DB.guilds.find({f"codes.{game.value}.channel": {"$ne": None}}, {"_id": 0, "id": 1})
        translations, embeds, view = cls._pre_translate(codes, game)
        async for guild_data in notifies:
            try:
                role = None
                guild = await Guild.new(guild_data["id"])

                mention_role: bool = guild.codes[game].mention_role is not None
                mention_everyone: bool = guild.codes[game].mention_everyone


                channel_id = guild.codes[game].channel
                if channel_id is None:
                    continue

                channel = cls._client.get_channel(channel_id) or await cls._client.fetch_channel(channel_id)
                if not channel:
                    await guild._update_module_setting(
                        "codes",
                        game,
                        "channel",
                        None
                    )
                    continue

                role_id = guild.codes[game].mention_role
                if role_id is not None:
                    guild_obj = cls._client.get_guild(guild.id) or await cls._client.fetch_guild(guild.id)
                    role = guild_obj.get_role(role_id)
                
                if not role:
                    # Update DB to remove invalid role
                    await guild._update_module_setting(
                        "codes",
                        game,
                        "mention_role",
                        None
                    )
                    mention_role = False
                
                send_msg = f"{role.mention + ' ' if mention_role and role else ''}{'@everyone ' if mention_everyone else ''}{translations[guild.language]['content']}"
                await channel.send(send_msg, embed=embeds[guild.language], view=view) # pyright: ignore
            except Exception as e:
                cls._client.capture_exception(e)