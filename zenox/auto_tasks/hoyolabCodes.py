import discord
import requests
import time
from discord.utils import MISSING
from typing import ClassVar
from ..bot.bot import Zenox
from ..static.enums import Game
from ..static.constants import HOYOLAB_GAME_IDS, GAME_THUMBNAILS
from ..db.structures import SpecialProgram, Code, CodeReward
from zenox.ui.hoyolab_codes.view import HoyolabCodesUI
from ..l10n import translator

class hoyolabCodes:
    """
    Possible states
    0 = Disabled Game
    1 = No Stream scheduled
    2 = Stream not yet live
    3 = Codes already Distributed
    4 = Codes haven't been found 
    5 = Codes have been found
    (Determined by if all codes are present (according to hoyoverse))
    """
    _bot: ClassVar[Zenox]
    _firstRun = True
    _STATES = ["Disabled", "No Schedule", "Not yet live", "Distributed", "Searching", "Found"]

    async def update_message(self):
        for game in Game:
            special_program = SpecialProgram(game, self._bot.config.auto_stream_codes_config[game].version)
            
            _, embed, _ = await special_program.buildMessage(self._bot, locale=discord.Locale("en-US"))
            view = HoyolabCodesUI(author=None, data=special_program, locale=discord.Locale("en-US"))
            attachments = [discord.File("./zenox-assets/assets/genshin-impact/thumbnails/" + GAME_THUMBNAILS[special_program.game], filename="thumbnail.png")]

            STATE = self._get_state(self, game, self._bot.config.auto_stream_codes_config[game].version)
            CHANNEL = self._bot.get_channel(self._bot.config.auto_stream_codes_config[game].channel)
            MESSAGE = CHANNEL.get_partial_message(self._bot.config.auto_stream_codes_config[game].message)
            await MESSAGE.edit(content=f"State `{STATE}` `{self._STATES[STATE]}` Version `{self._bot.config.auto_stream_codes_config[game].version}` Next Update <t:{round(time.time()+180)}:R>", embed=embed, attachments=attachments, view=view)


    def _get_header(self, gameID: int):
        HEADERS = {
            "authority": "bbs-api-os.hoyolab.com",
            "method": "GET",
            "path": f"/community/painter/wapi/circle/channel/guide/material?game_id={gameID}",
            "scheme": "https",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-DE,en;q=0.9,de-DE;q=0.8,de;q=0.7,en-GB;q=0.6,en-US;q=0.5,zh-CN;q=0.4,zh;q=0.3",
            "origin": "https://www.hoyolab.com",
            "referer": "https://www.hoyolab.com/",
            "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "x-rpc-app_version": "3.1.0",
            "x-rpc-client_type": "5",
            "x-rpc-hour": "18",
            "x-rpc-language": "en-us",
            "x-rpc-page_info": '{"pageName":"","pageType":"","pageId":"","pageArrangement":"","gameId":""}',
            "x-rpc-page_name": "",
            "x-rpc-show-translated": "False",
            "x-rpc-source_info": '{"sourceName":"","sourceType":"","sourceId":"","sourceArrangement":"","sourceGameId":""}',
            "x-rpc-sys_version": "Windows NT 10.0",
            "x-rpc-timezone": "Europe/Berlin",
            "x-rpc-weekday": "5"
        }
        return HEADERS
    async def _api_request(self, game: Game):
        print(f"Sent Hoyolab request for {game.value}")
        _url = f"https://bbs-api-os.hoyolab.com/community/painter/wapi/circle/channel/guide/material?game_id={HOYOLAB_GAME_IDS[game]}"

        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
        })
        response = session.get(_url, headers=self._get_header(self, HOYOLAB_GAME_IDS[game]))
        response.raise_for_status()
        resp_json = response.json()
        return resp_json
    
    def _parse_data(self, response_data, special_program: SpecialProgram):
        module_data = None
        # Check if Module 7 exists in data (7 = Stream Codes)
        for i, module in enumerate(response_data['data']['modules']):
            if module['module_type'] != 7:
                continue
            module_data = module
        
        if not module_data:
            return False
        
        TOTAL_CODES: int = module_data['exchange_group']['bonuses_summary']['code_count']
        if not module_data['exchange_group']['bonuses']:
            return False

        for code_data in module_data['exchange_group']['bonuses']:
            if not code_data['exchange_code']:
                continue
            code: Code = Code(game=special_program.game, code=code_data['exchange_code'])
            if code.expire_unix != code_data['offline_at']:
                code._update_val("expire_unix", code_data['offline_at'])
            if not code.discovered_unix:
                code._update_val("discovered_unix", round(time.time()))
            if code.is_china == None:
                code.is_china = False 
            special_program.addCode(code)
        if TOTAL_CODES != len(special_program.codes):
            return False
        return True
    
    def _get_state(self, game: Game, version: str):
        if self._bot.config.auto_stream_codes_config[game].disabled: # Disabled Game
          return 0
        elif self._bot.config.auto_stream_codes_config[game].stream_time == 0: # No Stream scheduled
          return 1
        elif self._bot.config.auto_stream_codes_config[game].stream_time - time.time() > 0: # Stream hasn't started yet
          return 2
        elif SpecialProgram(game, version).published: # Codes have been distributed already
          return 3
        elif SpecialProgram(game, version).found: # Codes have been found
            return 5
        return 4

    @classmethod
    async def execute(self, client: Zenox):
        self._bot = client
        
        for game in Game:
            _state = self._get_state(self, game, self._bot.config.auto_stream_codes_config[game].version)
            if _state not in [4, 5]:
              continue
            special_program = SpecialProgram(game, self._bot.config.auto_stream_codes_config[game].version)

            if _state == 4: # No need to send request, if we already know the codes
              response_data = await self._api_request(self, game)
              res = self._parse_data(self, response_data, special_program)
              if res:
                  special_program.mark("found")
        await self.update_message(self)