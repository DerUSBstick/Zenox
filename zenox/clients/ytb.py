from __future__ import annotations

import os
import googleapiclient.discovery
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zenox.bot.bot import Zenox

API_SERVICE_NAME: str = "youtube"
API_VERSION: str = "v3"

class YTBClient:
    def __init__(self, client: Zenox) -> None:
        API_KEY = os.getenv("YOUTUBE_API_KEY")
        self.client = client
        self.youtube = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, developerKey=API_KEY
        )
    
    async def get_recent_channel_videos(self, channel_id: str, max_results: int = 5):
        request = self.youtube.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=max_results,
            order="date",
            type="video"
        )
        response = await self.client.loop.run_in_executor(self.client.executor, request.execute)
        return response.get("items", [])