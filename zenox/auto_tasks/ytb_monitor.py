from __future__ import annotations

import time
import discord
from typing import TYPE_CHECKING, ClassVar

from zenox.embeds import DefaultEmbed
from zenox.db.mongodb import DB
from zenox.db.classes import Guild
from zenox.enums import Game

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
    
    @classmethod
    async def execute(cls, client: Zenox) -> None:
        for game in Game:
            print(game)