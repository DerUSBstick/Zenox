from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, ClassVar

from zenox.enums import PrintColors

if TYPE_CHECKING:
    from ..bot import Zenox

class TopGG:
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    _url: ClassVar[str] = "https://top.gg/api/bots/781529450734551071/stats"
    
    @classmethod
    async def execute(cls, client: Zenox) -> None:
        if cls._lock.locked():
            print(f"[TopGG] Warning - {PrintColors.WARNING}TopGG is already running, skipping this execution.{PrintColors.ENDC}")
            return
        
        if client.session is None:
            return

        async with cls._lock:
            try:
                if token := client.config.topgg_token:
                    headers = {"Authorization": f"Bearer {token}"}
                    data = {"server_count": len(client.guilds)}

                    await client.session.post(cls._url, json=data, headers=headers)
                    print(f"[TopGG] Info - {PrintColors.OKGREEN}Successfully posted stats to TopGG.{PrintColors.ENDC}")
                else:
                    print(f"[TopGG] Warning - {PrintColors.WARNING}TopGG token not provided or HTTP session not initialized, skipping posting stats.{PrintColors.ENDC}")
            except Exception as e:
                print(f"[TopGG] Error - {PrintColors.FAIL}Failed to post stats to TopGG: {e}{PrintColors.ENDC}")
