from __future__ import annotations

from dataclasses import dataclass

from ..mongodb import DB
from ...enums import Game

__all__ = ("RedemptionCode",)

@dataclass
class RedemptionCode:
    code: str
    game: Game
    published: bool

    @classmethod
    async def new(cls, code: str, game: Game) -> RedemptionCode:
        data = await DB.codes.find_one({"code": code, "game": game.value})
        if data is None:
            await cls.add_empty(code, game, False)
            data = await DB.codes.find_one({"code": code, "game": game.value})

        assert data is not None

        instance = RedemptionCode(
            code=data["code"],
            game=Game(data["game"]),
            published=data["published"],
        )

        return instance
    
    @classmethod
    async def add_empty(cls, code: str, game: Game, published: bool) -> None:
        await DB.codes.insert_one({
            "code": code,
            "game": game.value,
            "published": published
        })