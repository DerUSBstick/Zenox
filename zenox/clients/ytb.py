from __future__ import annotations

import googleapiclient.discovery
from typing import TYPE_CHECKING, TypedDict, List, cast, Required, Dict
from feedparser import parse

if TYPE_CHECKING:
    from zenox.bot.bot import Zenox

API_SERVICE_NAME: str = "youtube"
API_VERSION: str = "v3"

class RSSEntry(TypedDict, total=False):
    """Only need video ID here"""
    yt_videoid: Required[str]
    title: Required[str] # Temporarily needed for logging

class RSSFeed(TypedDict, total=False):
    entries: Required[List[RSSEntry]]
    feed: dict

class VideoDetails(TypedDict, total=False):
    kind: str
    etag: str
    id: Required[str]
    snippet: Required[VideoSnippet]
    liveStreamingDetails: VideoLiveStreamingDetails

class VideoSnippet(TypedDict, total=False):
    publishedAt: Required[str]
    channelId: str
    title: Required[str]
    description: Required[str]
    thumbnails: VideoThumbnails
    channelTitle: Required[str]
    categoryId: str
    liveBroadcastContent: Required[str]
    defaultLanguage: str
    localized: Dict[str, str]
    defaultAudioLanguage: str

class VideoThumbnails(TypedDict, total=False):
    default: VideoThumbnailDetails
    medium: VideoThumbnailDetails
    high: VideoThumbnailDetails
    standard: VideoThumbnailDetails
    maxres: VideoThumbnailDetails

class VideoThumbnailDetails(TypedDict, total=False):
    url: str
    width: int
    height: int

class VideoLiveStreamingDetails(TypedDict, total=False):
    actualStartTime: str
    actualEndTime: str
    scheduledStartTime: str

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

        feed = parse(xml)
        return cast(RSSFeed, feed)

    async def get_video_details(self, video_id: str) -> List[VideoDetails] | None:
        request = self.youtube.videos().list(
            part="snippet,liveStreamingDetails",
            id=video_id,
        )
        response = await self.client.loop.run_in_executor(self.client.executor, request.execute)
        if response.get("items") is None or len(response.get("items", [])) == 0:
            return None
        return cast(List[VideoDetails], response.get("items", []))