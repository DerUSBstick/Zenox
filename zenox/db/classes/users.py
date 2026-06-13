from __future__ import annotations

import discord
from dataclasses import dataclass
from typing import Any, ClassVar, Dict

from .accounts import GameAccount
from ..mongodb import DB
from ...enums import Game

__all__ = ("UserConfig",)


@dataclass
class UserConfig:
    id: int
    features: list[str]
    flags: list[str]
    language: discord.Locale

    # Accounts
    accounts: list[GameAccount]

    cache: ClassVar[Dict[int, UserConfig]] = {}

    @classmethod
    async def new(cls, user_id: int) -> UserConfig:
        if user_id in cls.cache:
            return cls.cache[user_id]

        data = await DB.users.find_one({"id": user_id})
        if data is None:
            await cls.add_empty(user_id)
            data = await DB.users.find_one({"id": user_id})

        assert data is not None

        instance = UserConfig(
            id=data["id"],
            features=data["features"],
            flags=data["flags"],
            language=discord.Locale(data["language"]),
            accounts=[
                GameAccount(**data["accounts"][game]) for game in data["accounts"]
            ]
        )

        cls.cache[user_id] = instance
        return instance

    @classmethod
    async def add_empty(cls, user_id: int) -> None:
        await DB.users.insert_one({
            "id": user_id,
            "features": [],
            "flags": [],
            "language": "en-US",
            "accounts": {}
        })

    async def _update_val(self, key: str, value: Any, operator: str = "$set") -> None:
        await DB.users.update_one({"id": self.id}, {operator: {key: value}})

        # Update the cache for direct class attributes (non-nested fields)
        if "." not in key:
            setattr(self, key, value)
    
    async def _add_account(self, game: Game, account: GameAccount) -> None:
        self.accounts.append(account)
        await DB.accounts.insert_one(account.to_dict())
        await DB.users.update_one({"id": self.id}, {"$push": {"accounts": {"uid": account.uid, "game": game.value}}})
        
    async def _remove_account(self, account: GameAccount) -> None:
        self.accounts.remove(account)
        await DB.accounts.delete_one({"uid": account.uid, "game": account.game.value})
        await DB.users.update_one({"id": self.id}, {"$pull": {"accounts": {"uid": account.uid, "game": account.game.value}}})