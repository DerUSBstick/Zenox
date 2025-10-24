from __future__ import annotations

import os
import googleapiclient.discovery
from typing import TYPE_CHECKING, TypedDict, List, Any, cast, Required
from feedparser import parse

if TYPE_CHECKING:
    from zenox.bot.bot import Zenox

API_SERVICE_NAME: str = "youtube"
API_VERSION: str = "v3"

class RSSEntry(TypedDict, total=False):
    title: str
    link: str
    published: str
    published_parsed: Any
    yt_videoid: Required[str]
    author: str

class RSSFeed(TypedDict, total=False):
    entries: Required[List[RSSEntry]]
    feed: dict

class YTBClient:
    def __init__(self, client: Zenox) -> None:
        API_KEY = client.config.youtube_api_key
        self.client = client
        self.youtube = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, developerKey=API_KEY
        )
    
    async def get_recent_channel_videos_rss(self, channel_id: str) -> RSSFeed:
        assert self.client.session is not None, "Client session is not initialized."

        rss_feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        # Fetch and parse in function
        async with self.client.session.get(rss_feed_url) as response:
            xml = await response.text()

        feed = await self.client.loop.run_in_executor(self.client.executor, lambda: parse(xml))
        return cast(RSSFeed, feed)

    async def get_recent_channel_videos(self, channel_id: str, max_results: int = 5):
        request = self.youtube.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=max_results,
            order="date",
            type="video"
        )
        # Need to apply liveBroadcastContent filter later
        response = await self.client.loop.run_in_executor(self.client.executor, request.execute)
        return response.get("items", [])

    async def get_upcoming_streams(self, channel_id: str, max_results: int = 1):
        request = self.youtube.search().list(
            part="snippet",
            channelId=channel_id,
            maxResults=max_results,
            eventType="upcoming",
            type="video"
        )
        response = await self.client.loop.run_in_executor(self.client.executor, request.execute)
        return response.get("items", [])

    async def get_video_details(self, video_id: str):
        request = self.youtube.videos().list(
            part="snippet,liveStreamingDetails",
            id=video_id,
            # fields="items(snippet(thumbnails))"
        )
        response = await self.client.loop.run_in_executor(self.client.executor, request.execute)
        return response.get("items", [])