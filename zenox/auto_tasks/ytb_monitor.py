from __future__ import annotations

import asyncio
import datetime
from typing import TYPE_CHECKING, ClassVar

from zenox.db.mongodb import DB
from zenox.db.classes import Guild, Video
from zenox.ui.components import URLButtonView
from zenox.enums import Game
from zenox.constants import GAME_YOUTUBE_CHANNEL_ID
from zenox.clients.ytb import YTBClient, VideoDetails
from zenox.l10n import LocaleStr, translator

if TYPE_CHECKING:
    from ..bot import Zenox

"""Strategy
1. Loop through Games
2. For each game, fetch RSS-Feed of its YouTube Channel
3. Check Database through a RAW Query if video_id exists
4. Get Video Details from YouTube API
5. If video is a upcoming Livestream, schedule a Stream for all Guilds and internally in the Bots Database
6. If it's a normal video, notify all Guilds that have Notifications enabled for that Game
7. If not, create a new entry using zenox.db.classes.videos.Video

"""

class YTBMonitor:
    _after_date: datetime.datetime = datetime.datetime(2025, 11, 14, 4, 0, 20) # Avoid backfill of old videos
    _client: ClassVar[Zenox]
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()
    
    @classmethod
    async def execute(cls, client: Zenox) -> None:
        if cls._lock.locked():
            print("YTBMonitor is already running, skipping this execution.")
            return
        
        async with cls._lock:
            cls._client = client
            ytbclient = YTBClient(client)
            for game in Game:
                feed = await ytbclient.get_recent_channel_videos_rss(
                    GAME_YOUTUBE_CHANNEL_ID[game]
                )
                for entry in feed["entries"]:
                    # if entry["yt_videoid"] not in ["Sx7xZp96nZM", "j8i2c-ZMFJY"]:
                    #     continue
                    if any("shorts" in link["href"] for link in entry["links"]):
                        # print("Skipping Shorts video:", entry["yt_videoid"])
                        continue
                    db_res = await DB.videos.find_one({"video_id": entry["yt_videoid"], "game": game.value})
                    if db_res is not None:
                        continue  # Video already processed
                    # print(entry["yt_videoid"], entry['title'])
                    videos = await ytbclient.get_video_details(entry["yt_videoid"])
                    if videos is None:
                        continue # Video not found
                    elif videos[0]["snippet"]["publishedAt"] < cls._after_date.isoformat() + "Z":
                        continue  # Video is older than after_date
                    elif videos[0]["snippet"]["liveBroadcastContent"] == "upcoming" and videos[0].get("liveStreamingDetails") is not None:
                        """Upcoming Livestream"""
                        await cls.schedule_stream(videos[0])
                    elif videos[0]["snippet"]["liveBroadcastContent"] == "none" and videos[0].get("liveStreamingDetails") is not None:
                        """Past Livestream, ignore"""
                        continue
                    elif videos[0]["snippet"]["liveBroadcastContent"] == "none" and videos[0].get("liveStreamingDetails") is None:
                        """Normal Video"""
                        await cls.notify_video(videos[0], game)
                    else:
                        print("Unknown Video type")
                    
                    await asyncio.sleep(3)
                    # break
                    # print(video)
                    # print(video["liveStreamingDetails"])
    
    @classmethod
    async def schedule_stream(cls, video_data: VideoDetails) -> None:
        print("Scheduling stream:", video_data["id"])
        """Schedules a livestream for all guilds and internally in the database."""
        pass

    @classmethod
    async def notify_video(cls, video_data: VideoDetails, game: Game) -> None:
        """Notifies all guilds about a new video."""
        print("Notifying guilds about new video:", video_data["id"])

        notifies = DB.guilds.find({f"youtube_notifications.{game.value}.channel": {"$ne": None}}, {"_id": 0, "id": 1})
        async for guild_data in notifies:
            try:
                role = None
                guild = await Guild.new(guild_data["id"])

                channel_id = guild.youtube_notifications[game].channel
                if channel_id is None:
                    continue

                channel = cls._client.get_channel(channel_id) or await cls._client.fetch_channel(channel_id)
                
                role_id = guild.youtube_notifications[game].mention_role
                if role_id is not None:
                    guild_obj = cls._client.get_guild(guild.id) or await cls._client.fetch_guild(guild.id)
                    role = guild_obj.get_role(role_id)
                
                if not role:
                    # Update DB to remove invalid role
                    await guild._update_module_setting(
                        "youtube_notifications",
                        game,
                        "mention_role",
                        None
                    )
                
                view = URLButtonView(guild.language, url=f"https://youtu.be/{video_data['id']}", label=LocaleStr(key="ytb_notification.watch_button.label"))

                msg = translator.translate(
                    LocaleStr(key="ytb_notification.content", channel=video_data["snippet"]["channelTitle"], url=f"https://youtu.be/{video_data['id']}"),
                    locale=guild.language,
                )
                send_msg = f"{role.mention + ' ' if role else ''}{'@everyone' + ' ' if guild.youtube_notifications[game].mention_everyone else ''}{msg}"
                await channel.send(send_msg, view=view) # pyright: ignore[reportAttributeAccessIssue]

                print(guild.id)
            except Exception as e:
                cls._client.capture_exception(e)

        # Finally, add video to database
        await Video.new(
            video_id=video_data["id"],
            game=game,
            title=video_data["snippet"]["title"],
        )
    