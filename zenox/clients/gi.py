import genshin
import os
from zenox.db.structures import GameAccount
from zenox.static.utils import parse_cookie
from zenox.static.constants import ZX_GAME_TO_GPY_GAME

class GenshinClient(genshin.Client):
    def __init__(self, account: GameAccount) -> None:
        game = ZX_GAME_TO_GPY_GAME[account.game]
        cookies = parse_cookie(os.getenv("HOYOLAB_COOKIES"))
        cookies.pop("ltuid", None)
        cookies.pop("account_id", None)
        cookies.pop("ltuid_v2", None)
        cookies.pop("account_id_v2", None)
        super().__init__(
            cookies=cookies,
            game=game,
            uid=account.uid,
            # region=genshin.Region.OVERSEAS, # add .region to account at a later point, requires updating the linking process
            hoyolab_id=account.hoyolab_owner.hoyolab_id,
            cache=genshin.SQLiteCache(),
            debug=True
        )
        self._account = account