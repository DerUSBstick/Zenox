from __future__ import annotations

import discord
import datetime
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Literal

from ..mongodb import DB
from ...enums import Game

__all__ = ("GameAccount", "EnkaOwner", "LinkingEntryTemplate", "GameAccountTemplate")


@dataclass
class GameAccount:
    uid: str
    game: Game
    username: str
    public: bool
    linked_date: datetime.datetime
    user_id: int
    hoyolab_id: str | None
    enka_owner: EnkaOwner | None

    cache: ClassVar[Dict[str, GameAccount]] = {}

    @classmethod
    async def new(cls, uid: str, game: Game) -> GameAccount:
        cache_key = f"{game.value}_{uid}"
        if cache_key in cls.cache:
            return cls.cache[cache_key]
        
        data = await DB.accounts.find_one({"uid": uid, "game": game.value})
        if data is None:
            ...
        
        assert data is not None

        instance = GameAccount(
            uid=data["uid"],
            game=Game(data["game"]),
            username=data["username"],
            public=data["public"],
            linked_date=data["linked_date"],
            user_id=data["user_id"],
            hoyolab_id=data.get("hoyolab_id"),
            enka_owner=EnkaOwner(**data["enka_owner"]) if data.get("enka_owner") else None
        )
        cls.cache[cache_key] = instance
        return instance
    
    @classmethod
    async def add_empty(cls, uid: str, game: Game, username: str, public: bool, linked_date: datetime.datetime, user_id: int) -> None:
        await DB.accounts.insert_one({
            "uid": uid,
            "game": game.value,
            "username": username,
            "public": public,
            "linked_date": linked_date,
            "user_id": user_id,
            "hoyolab_id": None,
            "enka_owner": None
        })
    
    async def _update_val(self, key: str, value: Any, operator: str = "$set") -> None:
        await DB.accounts.update_one({"uid": self.uid, "game": self.game.value}, {operator: {key: value}})

        # Update the cache for direct class attributes (non-nested fields)
        if "." not in key:
            setattr(self, key, value)
        
    def to_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "game": self.game.value,
            "username": self.username,
            "public": self.public,
            "linked_date": self.linked_date,
            "user_id": self.user_id,
            "hoyolab_id": self.hoyolab_id,
            "enka_owner": self.enka_owner.to_dict() if self.enka_owner else None
        }


@dataclass
class EnkaOwner:
    userhash: str
    username: str

    def to_dict(self) -> dict[str, str]:
        return {
            "userhash": self.userhash,
            "username": self.username
        }

@dataclass
class LinkingEntryTemplate:
    method: Literal["UID", "Hoyolab"]
    hoyolab_id: str | None
    data: list[tuple[str, Game]]
    user_id: int
    started: datetime.datetime
    code: int
    interaction: discord.Interaction

class GameAccountTemplate(GameAccount):
    def __init__(self, uid: str, game: Game, username: str, public: bool, linked_date: datetime.datetime, user_id: int, hoyolab_id: str | None = None, enka_owner: EnkaOwner | None = None) -> None:
        self.uid: str = uid
        self.game: Game = game
        self.username: str = username
        self.public: bool = public
        self.linked_date: datetime.datetime = linked_date
        self.user_id: int = user_id
        self.hoyolab_id: str | None = hoyolab_id
        self.enka_owner: EnkaOwner | None = enka_owner