from __future__ import annotations

import asyncio
import time
import aiohttp
from typing import TYPE_CHECKING, ClassVar, TypedDict, Any, Required
import discord
from fake_useragent import UserAgent

from zenox import emojis
from zenox.constants import CODE_URLS, ZENOX_LOCALES, HOYO_REDEEM_URLS, GAME_THUMBNAILS, GAME_VALUABLES, GAME_TO_ID, HOYOLAB_STREAM_CODES_ENDPOINT
from zenox.db.mongodb import DB
from zenox.enums import Game
from zenox.embeds import Embed
from zenox.db.classes import Guild, RedemptionCode, SpecialProgram
from zenox.ui.components import View, Button
from zenox.l10n import LocaleStr
from zenox.ui.hoyolab_codes.view import HoyolabCodesUI

if TYPE_CHECKING:
    from ..bot import Zenox

class CodeData(TypedDict):
    code: Required[str]
    game: Required[str]
    status: Required[str]
    rewards: Required[str]

class CodeFetchResult(TypedDict):
    codes: Required[list[CodeData]]
    game: Required[str]

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
    async def _get_stream_codes(
        cls,
        session: aiohttp.ClientSession,
        game: Game,
    ) -> dict[str, Any]:
        try:
            async with session.get(
                HOYOLAB_STREAM_CODES_ENDPOINT.format(game_id=GAME_TO_ID[game]),
                headers={"User-Agent": cls._ua.random},
            ) as response:
                response.raise_for_status()
                data = await response.json()

            return data
        except Exception as e:
            print(f"Failed to fetch stream codes for {game.value}: {e}")
            cls._client.capture_exception(e)
            # fallback shape
            return {"retcode": -1, "message": str(e), "data": {"modules": [], "in_feed_modules": [], "server_time": "0"}}

    @classmethod
    async def _handle_non_stream_codes(cls, session: aiohttp.ClientSession, game: Game) -> None:
        codes = await cls._get_codes(session, game)
        published_codes: list[dict[str, str]] = []
        for code_data in codes["codes"]:
            if code_data["status"] != "OK":
                continue
            redemption_code = await RedemptionCode.new(code=code_data["code"], game=game)

            if not redemption_code.published:
                published_codes.append({"code": code_data["code"]})
                redemption_code.published = True
                await DB.codes.update_one({"code": redemption_code.code, "game": redemption_code.game.value}, {"$set": {"published": True}})
                            
        if published_codes:
            await cls.notify_codes(game, published_codes)
        print(f"Published codes for {game.name}: {published_codes}")
    
    @classmethod
    async def _update_message(cls, channel_id: int, message_id: int, special_program: SpecialProgram, *, client: Zenox | None = None, embed_only: bool = False) -> None:
        client = client or cls._client
        print(f"Updating message for channel {channel_id} and message {message_id} with game {special_program.game.value} stream codes. Codes: {special_program.codes}")
        try:
            channel = client.get_channel(channel_id) or await client.fetch_channel(channel_id)
            if not channel:
                raise ValueError(f"Channel with ID {channel_id} not found.")
            
            assert isinstance(channel, discord.TextChannel)
            assert client.db_config is not None, "Bot configuration is not loaded yet."
            
            codes_str = "".join([f"> `{code.code}` | **[Redeem Here]({HOYO_REDEEM_URLS[special_program.game] + code.code})**\n" for code in special_program.codes]) or "No codes found yet\n"

            message = await channel.fetch_message(message_id)

            embed = Embed(locale=discord.Locale.american_english, title=LocaleStr(key="stream_codes_message.embed.title", version=special_program.version), description=LocaleStr(key="stream_codes_message.embed.description", emj1=emojis.ANNOUNCEMENT, emj2=emojis.BLURPLE_LINK).translate(discord.Locale.american_english))
            embed.set_thumbnail(url=GAME_THUMBNAILS[special_program.game])
            embed.add_field(name=emojis.CODES1+emojis.CODES2+emojis.CODES3, value=codes_str)
            if special_program.stream_late_image:
                embed.set_image(url=special_program.stream_late_image)

            view = HoyolabCodesUI(author=None, locale=discord.Locale.american_english, data=special_program)

            msg_content = f"State: `{client.db_config.stream_codes_config[special_program.game].state}` Version: `{client.db_config.stream_codes_config[special_program.game].version}` Next Update <t:{round(time.time()+300)}:R>"
            
            if embed_only:
                await message.edit(embed=embed)
            else:
                await message.edit(content=msg_content, embed=embed, view=view)
        
        except Exception as e:
            client.capture_exception(e)

    
    @classmethod
    async def _handle_hoyolab_codes(cls, session: aiohttp.ClientSession, game: Game, special_program: SpecialProgram) -> None:
        if special_program.codes_count != 0 and special_program.codes_count == len(special_program.codes):
            print(f"Codes for {game.value} stream already up to date. Skipping fetch.")
            return
        codes = await cls._get_stream_codes(session, game)
        module_data: dict[str, Any] | None = None
        for module in codes["data"]["modules"]:
            if module["module_type"] != 7:
                continue
            module_data = module
            print(module)
 
        if not module_data or not module_data["exchange_group"]["bonuses"]:
            return

        if int(module_data["exchange_group"]["bonuses_summary"]["code_count"]) != special_program.codes_count:
            await special_program._update_val("codes_count", module_data["exchange_group"]["bonuses_summary"]["code_count"])

        published_codes: list[dict[str, str]] = []
        for bonus in module_data["exchange_group"]["bonuses"]:
            if not bonus["exchange_code"]:
                continue
            published_codes.append({"code": bonus["exchange_code"]})
            redemption_code = await RedemptionCode.new(code=bonus["exchange_code"], game=game)
            if not redemption_code.published:
                await special_program._add_code(redemption_code)
                redemption_code.published = True
                await DB.codes.update_one({"code": redemption_code.code, "game": redemption_code.game.value}, {"$set": {"published": True}})
        print(f"Published stream codes for {game.value}: {published_codes}")

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
                try:
                    if client.db_config.stream_codes_config[game].stream_time - int(time.time()) < 3600 and client.db_config.stream_codes_config[game].state != 5 and client.db_config.stream_codes_config[game].stream_time != 0:
                        print(f"Stream codes for {game.value} are going live within an hour or already live. Fetching stream codes.")
                        special_program = await SpecialProgram.new(game=game, version=client.db_config.stream_codes_config[game].version)
                        await cls._handle_hoyolab_codes(client.session, game, special_program)
                    else:
                        await cls._handle_non_stream_codes(client.session, game)
                except Exception as e:
                    client.capture_exception(e)
                finally:
                    try:
                        special_program = await SpecialProgram.new(game=game, version=client.db_config.stream_codes_config[game].version)
                        await cls._update_message(client.db_config.stream_codes_config[game].channel, client.db_config.stream_codes_config[game].message, special_program)
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
                DESC += f"> `{code['code']}` | **[{DIRECT_LINK}]({HOYO_REDEEM_URLS[game]+code['code']})**\n"
                if not VIEW_POPULATED:
                    _view.add_item(Button(label=code["code"], url=HOYO_REDEEM_URLS[game]+code["code"]))
            
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