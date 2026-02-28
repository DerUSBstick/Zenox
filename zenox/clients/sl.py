from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, cast

if TYPE_CHECKING:
    from zenox.bot.bot import Zenox

class SeelelandResponse(TypedDict, total=False):
    account: AccountData
    leaderboard: dict[str, SeelelandLeaderboardData]
    
class AccountData(TypedDict, total=False):
    id: str
    nm: str
    ach: int
    achrank: str

class SeelelandLeaderboardData(TypedDict, total=False):
    sc: int
    rank: str
    percrank: str
    percraw: float

class SLClient:
    """A Client for interacting with Seeleland API"""

    def __init__(self, client: Zenox) -> None:
        self.client = client
        self.base_url = client.config.seeleland_api_url
    
    async def get_player_data(self, uid: str) -> SeelelandResponse:
        """Fetch player data from Seeleland API by UID"""

        assert self.client.session is not None, "Client session is not initialized"

        url = self.base_url + f"/getPlayer?uid={uid}"
        async with self.client.session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            
            # Extract account data (k="p") and leaderboard data from characters
            account = cast(AccountData, next((item for item in data if item.get("k") == "p"), {}))
            
            leaderboard = cast(
                dict[str, SeelelandLeaderboardData],
                {
                    f"{item['k']}_{lb_key}": lb_value
                    for item in data
                    if "lb" in item and item.get("k") != "p"
                    for lb_key, lb_value in item["lb"].items()
                }
            )
            
            return SeelelandResponse(account=account, leaderboard=leaderboard)