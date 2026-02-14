from __future__ import annotations

import discord
from dataclasses import dataclass
from typing import Any, ClassVar, Dict

from ..mongodb import DB
from ...enums import Game

__all__ = ("Guild", "CodesModule", "ReminderModule")


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
    youtube_notifications: dict[Game, YTNotificationsModule]

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
                Game(game): CodesModule(**data["codes"][game]) for game in data["codes"]
            },
            reminders={
                Game(game): ReminderModule(**data["reminders"][game])
                for game in data["reminders"]
            },
            youtube_notifications={
                Game(game): YTNotificationsModule(**data["youtube_notifications"][game])
                for game in data["youtube_notifications"]
            },
        )

        cls.cache[guild_id] = instance
        return instance

    @classmethod
    async def delete(cls):
        if cls.id in cls.cache:
            del cls.cache[cls.id]
        await DB.guilds.delete_one({"id": cls.id})

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
                    }
                    for game in Game
                },
                "reminders": {
                    game.value: {"setup": False, "stream_reminder": False}
                    for game in Game
                },
                "youtube_notifications": {
                    game.value: {
                        "setup": False,
                        "channel": None,
                        "mention_everyone": False,
                        "mention_role": None,
                    }
                    for game in Game
                },
            }
        )

    async def _update_val(self, key: str, value: Any, operator: str = "$set") -> None:
        await DB.guilds.update_one({"id": self.id}, {operator: {key: value}})

        # Update the cache for direct class attributes (non-nested fields)
        if "." not in key:
            setattr(self, key, value)

    async def _update_flags(self, flag: str, add: bool) -> None:
        if flag not in self.flags and add:
            self.flags.append(flag)
            await DB.guilds.update_one({"id": self.id}, {"$addToSet": {"flags": flag}})
        elif flag in self.flags and not add:
            self.flags.remove(flag)
            await DB.guilds.update_one({"id": self.id}, {"$pull": {"flags": flag}})

    async def _update_language(self, locale: discord.Locale) -> None:
        await DB.guilds.update_one(
            {"id": self.id}, {"$set": {"language": locale.value}}
        )
        self.language = locale

    async def _update_module_setting(
        self,
        module_name: str,
        game: Game,
        setting: str,
        value: Any,
        operator: str = "$set",
    ) -> None:
        """Update a specific setting for a module"""
        key = f"{module_name}.{game.value}.{setting}"
        # Update in Database
        await self._update_val(key, value, operator)

        # Update in Cache
        module = getattr(self, module_name)
        setattr(module[game], setting, value)

    def has_flag(self, flag: str) -> bool:
        return flag in self.flags


@dataclass
class CodesModule:
    setup: bool
    channel: int | None
    mention_everyone: bool
    mention_role: int | None


@dataclass
class ReminderModule:
    setup: bool
    stream_reminder: bool

@dataclass
class YTNotificationsModule:
    setup: bool
    channel: int | None
    mention_everyone: bool
    mention_role: int | None