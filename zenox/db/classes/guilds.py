from __future__ import annotations

import discord
from dataclasses import dataclass
from typing import ClassVar, Dict

from ..mongodb import DB
from ...enums import Game


@dataclass
class Guild:
    id: int
    features: list[str]
    flags: list[str]
    language: discord.Locale
    member_count: int | None
    # Modules
    codes: dict[Game, CodesModule]
    reminders: dict[Game, ReminderModule]

    cache: ClassVar[Dict[int, Guild]] = {}

    @classmethod
    async def new(cls, guild_id: int):
        if guild_id in cls.cache:
            return cls.cache[guild_id]

        data = await DB.guilds.find_one({"id": guild_id})
        if data is None:
            await cls.add_empty(guild_id)
            data = await DB.guilds.find_one({"id": guild_id})
        
        assert data is not None
        
        instance = Guild(
            id=data["id"],
            features=data["features"],
            flags=data["flags"],
            language=discord.Locale(data["language"]),
            member_count=data["member_count"],
            codes={
                Game(game): CodesModule(**data["codes"][game])
                for game in data["codes"]
            },
            reminders={
                Game(game): ReminderModule(**data["reminders"][game])
                for game in data["reminders"]
            },
        )

        cls.cache[guild_id] = instance
        return instance


    @classmethod
    async def add_empty(cls, guild_id: int):
        await DB.guilds.insert_one(
            {
                "id": guild_id,
                "features": [],
                "flags": [],
                "language": "en-US",
                "member_count": None,
                "codes": {
                    game.value: {
                        "setup": False,
                        "channel": None,
                        "mention_everyone": False,
                        "mention_role": None,
                        "ping_premium_only": True,
                    }
                    for game in Game
                },
                "reminders": {
                    game.value: {"setup": False, "stream_reminder": False}
                    for game in Game
                },
            }
        )


@dataclass
class CodesModule:
    setup: bool
    channel: int | None
    mention_everyone: bool
    mention_role: int | None
    ping_premium_only: bool


@dataclass
class ReminderModule:
    setup: bool
    stream_reminder: bool
