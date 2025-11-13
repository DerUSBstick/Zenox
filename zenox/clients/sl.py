from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zenox.bot.bot import Zenox

class SLClient:
    """A Client for interacting with Seeleland API"""

    def __init__(self, client: Zenox) -> None:
        self.client = client
        self.base_url = client.config.seeleland_api_url
    
    async def get_player_data(self, uid: str) -> dict:
        """Fetch player data from Seeleland API by UID"""

        assert self.client.session is not None, "Client session is not initialized"

        url = self.base_url + f"get_player_data?uid={uid}"
        async with self.client.session.get(url) as response:
            return await response.json()