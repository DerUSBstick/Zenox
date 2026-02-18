from __future__ import annotations

import discord

from dataclasses import dataclass
from typing import Any

from ..mongodb import DB
from ...enums import Game

__all__ = ("SpecialProgram",)

@dataclass
class SpecialProgram:
    game: Game
    version: str
    stream_start_time: int
    stream_end_time: int
    stream_title: str
    stream_early_image: bytes
    stream_reminder_published: bool = False

    @classmethod
    async def new(cls, game: Game, version: str, *, stream_start_time: int = 0, stream_end_time: int = 0, stream_title: str = "", stream_early_image: discord.Attachment) -> SpecialProgram:
        data = await DB.special_programs.find_one({"game": game.value, "version": version})
        if data is None:
            image = await stream_early_image.read()
            await cls.add_empty(game, version, stream_start_time=stream_start_time, stream_end_time=stream_end_time, stream_title=stream_title, stream_early_image=image)
            data = await DB.special_programs.find_one({"game": game.value, "version": version})

        assert data is not None

        instance = SpecialProgram(
            game=Game(data["game"]),
            version=data["version"],
            stream_start_time=data["stream_start_time"],
            stream_end_time=data["stream_end_time"],
            stream_title=data["stream_title"],
            stream_early_image=data["stream_early_image"],
            stream_reminder_published=data["stream_reminder_published"]
        )

        return instance

    @classmethod
    async def add_empty(cls, game: Game, version: str, *, stream_start_time: int = 0, stream_end_time: int = 0, stream_title: str = "", stream_early_image: bytes) -> None:
        await DB.special_programs.insert_one({
            "game": game.value,
            "version": version,
            "stream_start_time": stream_start_time,
            "stream_end_time": stream_end_time,
            "stream_title": stream_title,
            "stream_early_image": stream_early_image,
            "stream_reminder_published": False
        })
    
    async def _update_val(self, key: str, value: Any, operator: str = "$set") -> None:
        await DB.special_programs.update_one({"game": self.game.value, "version": self.version}, {operator: {key: value}})
        setattr(self, key, value)