from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..mongodb import DB
from ...enums import Game

__all__ = ("ModuleConfig", "StreamCodesConfig")

@dataclass
class ModuleConfig:
    """Global configuration for the bot. This is not guild-specific."""
    stream_codes_config: dict[Game, StreamCodesConfig]

    @classmethod
    async def new(cls):
        data = await DB.config.find_one({"_id": "global_config"})
        if data is None:
            await cls.add_empty()
            data = await DB.config.find_one({"_id": "global_config"})

        assert data is not None

        instance = ModuleConfig(
            stream_codes_config={
                Game(game): StreamCodesConfig(**data["stream_codes_config"][game]) for game in data["stream_codes_config"]
            }
        )

        return instance
    
    @classmethod
    async def add_empty(cls) -> None:
        await DB.config.insert_one({
            "_id": "global_config",
            "stream_codes_config": {
                game.value: {
                    "channel": None,
                    "message": None,
                    "stream_time": 0,
                    "version": None,
                    "state": 0
                } for game in Game
            }
        })
    
    async def _update_val(self, key: str, value: Any, operator: str = "$set") -> None:
        await DB.config.update_one({"_id": "global_config"}, {operator: {key: value}})

        # Update the cache for direct class attributes (non-nested fields)
        if "." not in key:
            setattr(self, key, value)
    
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


@dataclass
class StreamCodesConfig:
    channel: int
    message: int
    stream_time: int
    version: int
    state: int