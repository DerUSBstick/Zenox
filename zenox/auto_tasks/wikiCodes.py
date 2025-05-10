import re
import time, datetime
import discord
import genshin
import asyncio
import pandas as pd
from ..static.exceptions import WikiCodesHeaderMismatchError, WikiCodesDataMismatchError
from zenox.db.mongodb import ANALYTICSDB
from ..static.constants import Game, WIKI_PAGES, ZENOX_LOCALES, HOYO_REDEEM_URLS, GAME_THUMBNAILS
from ..l10n import LocaleStr
from ..static.embeds import Embed
from ..static.utils import get_emoji, send_webhook, redeem_code
from ..static import emojis
from ..db.structures import Code, CodeReward, GuildConfig, CodesConfig
from ..bot.bot import Zenox
from ..ui.components import View, Button

# Merge execute and check_publish into one function at a later point
class wikiCodes:
    
    _queued_codes: dict[Game, list[list[Code]]] = {}
    _limit = 4
    _stop: bool = False

    _blocked = ["HoYo FEST 2024", "Glad Tidings From Afar"]
    _blocked_lower = ["prime", "crucialgames", "steelseries", "alienware", "intel gaming access", "amd rewards", "giveaway)", "bundle", "twitch", "discord", "hoyofest", "hoyo fest"]
    _row_headers = ["Code", "Server", "Rewards", "Duration"]
    _servers = ['All', 'America, Europe, Asia, TW/HK/Macao', 'China', 'America', 'Asia', 'Europe', 'TW/HK/Macao']

    @classmethod
    def __init_vars(self):
        for game in Game:
            self._queued_codes[game] = []

    @classmethod
    def _get_codes(self, game: Game) -> pd.DataFrame:
        tables = pd.read_html(WIKI_PAGES[game])
        codes_data = tables[0]
        return codes_data

    @classmethod
    async def execute(self, client: Zenox):
        if self._stop:
            return
        try:
            _added_to_queue: list[Code] = []
            if not self._queued_codes:
                self.__init_vars()
            for game in Game:
                if not WIKI_PAGES[game]:
                    continue
                codes_data = self._get_codes(game)
                if len(self._row_headers) != len(codes_data.columns) or any(self._row_headers[i] != x for i, x in enumerate(codes_data)): # Verify Table Headers
                    raise WikiCodesHeaderMismatchError
                for code_data in codes_data.iterrows():
                    code_names = re.sub(r"\[.*", "", code_data[1].iloc[0]).replace("Quick Redeem", "").rstrip()
                    if any(x.lower() in self._blocked_lower for x in code_names.split(" ")) or code_names in self._blocked:
                        continue
                    code_server = code_data[1].iloc[1]
                    code_rewards = re.findall(r"([\w\s\-\'\(\)\"]+) ×(\d+(?:,\d{3})*)", code_data[1].iloc[2].replace("\"", ""))
                    code_infos = code_data[1].iloc[3]
                    if "Expired:" in code_infos:
                        continue
                    if not all(str(code).isalnum() for code in code_names.split(" ")):
                        continue
                    if code_server not in self._servers:
                        continue
                    codes: list[Code] = []

                    # Add Codes to Queue
                    for code in code_names.split(" "):
                        code: Code = Code(game=game, code=code)
                        if not code.discovered_unix:
                            code._update_val(key="discovered_unix", value=round(time.time()))
                        if not code.is_china:
                            code._update_val(key="is_china", value=code_server=="China")
                        if not code.rewards:
                            for reward in code_rewards:
                                code._add_reward(CodeReward(str(reward[0]).lstrip(), int(str(reward[1]).replace(",", ""))))
                        codes.append(code)
                    if not (codes[0].published or any(codes[0].code == x[0].code for x in self._queued_codes[game]) or codes[0].is_china or codes[0].redeemed is not None):
                        """Make sure code hasn't been published yet or is already in Queue"""
                        self._queued_codes[game].append((codes))
                        _added_to_queue.append(codes[0])

            if _added_to_queue:
                await send_webhook(
                    webhook_url=client.log_webhook_url,
                    username="WikiCodes Task",
                    content=f"Added {len(_added_to_queue)} Codes to Queue | Codes in Queue per Game: {', '.join([f'{game.value}: {len(self._queued_codes[game])}' for game in Game if self._queued_codes[game]])}",
                    embeds=[Embed(
                        locale=discord.Locale.american_english,
                        title="Added Codes",
                        description="\n".join([f"{code.code} | {code.game.value} | Rewards: {', '.join([f'{reward.reward} x{reward.amount}' for reward in code.rewards])}" for code in _added_to_queue]),
                        color=0x00ff00
                    )]
                )
            else:
                await send_webhook(
                    webhook_url=client.log_webhook_url,
                    username="WikiCodes Task",
                    content="No New Codes found in Wiki",
                    embeds=[Embed(
                        locale=discord.Locale.american_english,
                        title="No Codes Found",
                        color=0xff0000
                    )]
                )
        except Exception as e:
            client.capture_exception(e)
            await send_webhook(
                webhook_url=client.log_webhook_url,
                username="WikiCodes Task",
                content="Error while executing Task",
                embeds=[Embed(
                    locale=discord.Locale.american_english,
                    title="Error",
                    description=str(e),
                    color=0xff0000
                )]
            )

    @classmethod
    async def check_publish(self, client: Zenox):
        if self._stop:
            return
        
        if not self._queued_codes:
            self.__init_vars()
        # Bundles Rewards from all Codes together and initializes publishing
        # Function runs 2 hours after execute and calls a (new) function that returns the table to check if the code is still in there
        # If not remove the code before calculating rewards
        # If _codes is not empty initialize publishing
        # Limit of 5 codes per game per task run
        if not self._queued_codes:
            return

        for game in Game:
            if not WIKI_PAGES[game]:
                continue
            _curr_codes: list = [re.sub(r"\[.*", "", x[1].iloc[0]).replace("Quick Redeem", "").rstrip() for x in self._get_codes(game).iterrows()] # No need for filtering for blocked words, because they can't be present in the queue
            _rewards: list[CodeReward] = []
            _codes: list[Code] = []
            _removed: list[list[list[Code], int, str]] = []

            for i, queued_codes in enumerate(self._queued_codes[game].copy(), start=1):
                if i > self._limit:
                    break
                try:
                    await asyncio.sleep(5) # Rate limit for redeeming codes
                    await redeem_code(queued_codes[0].code, game)
                    queued_codes[0]._update_val("redeemed", True)
                except genshin.errors.GenshinException as e:
                    if e.retcode == -100:
                        await send_webhook(
                            webhook_url=client.log_webhook_url,
                            username="WikiCodes Task",
                            content="Invalid Cookies",
                            embeds=[Embed(
                                locale=discord.Locale.american_english,
                                title="Invalid Cookies",
                                description=str(e),
                                color=0xff0000
                            )]
                        )
                        self._stop = True
                        client.capture_exception(e)
                        return
                    elif isinstance(e, (genshin.errors.RedemptionClaimed, genshin.errors.RedemptionInvalid)) or e.retcode in [-2024, -2002, -2017]:
                        _removed.append((queued_codes, e.retcode, e.msg))
                    else:
                        self._stop = True
                        client.capture_exception(e)
                        return
                    index = self._queued_codes[game].index(queued_codes)
                    self._queued_codes[game].pop(index)
                    continue
                except Exception as e:
                    client.capture_exception(e)
                    self._stop = True
                    await send_webhook(
                        webhook_url=client.log_webhook_url,
                        username="WikiCodes Task",
                        content="Error while redeeming code",
                        embeds=[Embed(
                            locale=discord.Locale.american_english,
                            title="Error while redeeming code",
                            description=str(e),
                            color=0xff0000
                        )]
                    )
                    return
                _codes.append(queued_codes[0]) # Only add the first Code from the list as all the codes are tied together
                for reward in queued_codes[0].rewards:
                    _exist = False
                    for code_reward in _rewards:
                        if code_reward.reward == reward.reward:
                            _exist = True
                            code_reward.amount += reward.amount
                    if not _exist:
                        _rewards.append(reward)
            if _removed:
                for code in _removed:
                    for _code in code[0]:
                        _code._update_val("redeemed", False)
                await send_webhook(
                    webhook_url=client.log_webhook_url,
                    username="WikiCodes Task",
                    content="Removed Codes from Queue",
                    embeds=[Embed(
                        locale=discord.Locale.american_english,
                        title="Removed Codes",
                        description="\n".join([f"Code: {code[0][0].code} | Retcode: {code[1]} | Message: {code[2]}" for code in _removed]),
                        color=0xff0000
                    )]
                )
            if not _codes:
                continue
            _translations = self._pre_translate(game, _codes, _rewards)
            await self._publish(client, game, _codes, _translations)
            try:
                for code in _codes.copy():
                    if len(_codes) == 0:
                        break
                    if not self._queued_codes[game][0][0].code == code.code:
                        raise Exception
                    
                    for _code in self._queued_codes[game][0]:
                        _code._update_val("published", True)
                    code1 = _codes.pop(0)
                    code2 = self._queued_codes[game].pop(0)
                    assert code1.code == code2[0].code
            except Exception as e:
                client.capture_exception(e)
                self._stop = True
                await send_webhook(
                    webhook_url=client.log_webhook_url,
                    username="WikiCodes Task",
                    content="Error while removing Code from Queue",
                    embeds=[Embed(
                        locale=discord.Locale.american_english,
                        title="Error",
                        description=str(e),
                        color=0xff0000
                    )]
                )
    
    @classmethod
    def _pre_translate(self, game: Game, codes: list[Code], rewards: list[CodeReward]) -> dict[discord.Locale, dict[str, Embed | str]]:
        _translations: dict[discord.Locale, dict[str, Embed | str]] = {}
        for language in ZENOX_LOCALES:
            
            MESSAGE_CONTENT = LocaleStr(key="wikicodes.content").translate(language)
            EMBED_TITLE = LocaleStr(key="wikicodes_embed.title").translate(language)
            EMBED_FOOTER = LocaleStr(key="wikicodes_embed.footer", game=game.value).translate(language)
            REWARDS = LocaleStr(key="rewards").translate(language)
            DIRECT_LINK = LocaleStr(key="direct_link").translate(language)
            NO_ROLE_WARNING = LocaleStr(key="role_not_found_error").translate(language)
            
            DESC = f"\n{emojis.CODES1}{emojis.CODES2}{emojis.CODES3}\n"

            for code in codes:
                DESC += f"> {code.code} | **[{DIRECT_LINK}]({HOYO_REDEEM_URLS[game]+code.code})**\n"
            
            DESC += f"\n**〓 {REWARDS} 〓**\n"

            for reward in rewards:
                DESC += f"{get_emoji(reward.reward)} **{reward.reward} ×{reward.amount}**\n"

            embed = Embed(locale=language, title=EMBED_TITLE, description=DESC)
            embed.set_thumbnail(url="attachment://thumbnail.png")
            embed.set_footer(text=EMBED_FOOTER)


            _translations[language] = {"content": MESSAGE_CONTENT, "embed": embed, "norole": NO_ROLE_WARNING}
        return _translations

    @classmethod
    async def _publish(self, client: Zenox, game: Game, _codes: list[Code], _translations: dict[discord.Locale, dict[str, Embed | str]]) -> None:
        _success, _failed, _forbidden, _no_channel, _no_role = 0, 0, 0, 0, 0
        GUILDS = [guild["id"] for guild in client.db.guilds.find({})]
        view = View(author=None, locale=discord.Locale.american_english)
        for code in _codes:
            view.add_item(Button(label=code.code, url=HOYO_REDEEM_URLS[game]+code.code))
        for guild in GUILDS:
            try:
                guild = GuildConfig(guild)
                role = None
                displayWarning = False

                if not guild.codes_config[game].channel:
                    _no_channel += 1
                    continue

                if guild.codes_config[game].role_ping:
                    role = client.get_guild(guild.id).get_role(guild.codes_config[game].role_ping)
                    if not role:
                        displayWarning = True
                        guild.updateGameConfigValue(game, CodesConfig, "role_ping", None)
                        _no_role += 1
                
                content = f'{_translations[guild.language]["content"]} {role.mention if role else ""} {"@everyone" if guild.codes_config[game].everyone_ping else ""} {_translations[guild.language]["norole"] if displayWarning else ""}'
                ATTACHMENT = [discord.File("./zenox-assets/assets/genshin-impact/thumbnails/" + GAME_THUMBNAILS[game], filename="thumbnail.png")]

                channel = client.get_channel(guild.codes_config[game].channel)
                await channel.send(content=content, embed=_translations[guild.language]["embed"], files=ATTACHMENT, view=view)
                _success += 1
            except (discord.Forbidden, AttributeError):
                guild.updateGameConfigValue(game, CodesConfig, "channel", None)
                _forbidden += 1
            except Exception as e:
                client.capture_exception(e)
                _failed += 1
        
        await send_webhook(
            webhook_url=client.log_webhook_url,
            username="WikiCodes Task",
            content=f"Published {_success} Codes, {_failed} Failed, {_forbidden} Forbidden, {_no_channel} No Channel, {_no_role} No Role\nCodes in Queue for {game.value}: {len(self._queued_codes[game])-len(_codes)}",
            embeds=[Embed(
                locale=discord.Locale.american_english,
                title="Published Codes",
                description=f"Success: {_success}\nFailed: {_failed}\nForbidden: {_forbidden}",
                color=0x00ff00
            )]
        )

        ANALYTICSDB.wiki_codes.insert_one({
            "type": "send_wiki_codes",
            "game": game.value,
            "time": datetime.datetime.now(),
            "stats": {
                "success": _success,
                "failed": _failed,
                "forbidden": _forbidden,
                "no_channel": _no_channel,
                "no_role": _no_role
            }
        })