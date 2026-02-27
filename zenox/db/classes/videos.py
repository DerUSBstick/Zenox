from __future__ import annotations

import datetime
from dataclasses import dataclass

from ..mongodb import DB
from ...enums import Game

__all__ = ("Video",)

@dataclass
class Video:
    video_id: str
    game: Game
    title: str

    @classmethod
    async def new(cls, video_id: str, game: Game, title: str) -> Video:
        data = await DB.videos.find_one({"video_id": video_id, "game": game.value})
        if data is None:
            await cls.add_empty(video_id, game, title, datetime.date.today())
            data = await DB.videos.find_one({"video_id": video_id, "game": game.value})

        assert data is not None

        instance = Video(
            video_id=data["video_id"],
            game=Game(data["game"]),
            title=data["title"],
        )

        return instance
        
    
    @classmethod
    async def add_empty(cls, video_id: str, game: Game, title: str, date: datetime.date) -> None:
        # Convert date to datetime for BSON compatibility
        dt = datetime.datetime.combine(date, datetime.time.min, tzinfo=datetime.timezone.utc)
        await DB.videos.insert_one({
            "video_id": video_id,
            "game": game.value,
            "title": title,
            "date": dt
        })