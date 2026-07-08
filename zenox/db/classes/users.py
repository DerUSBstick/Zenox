from __future__ import annotations

import contextlib
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

    @staticmethod
    async def _parse_accounts(raw_accounts: Any) -> list[GameAccount]:
        """Parse account data from both legacy and current schema shapes.

        Legacy shape: dict[str, account_payload]
        Current shape: list[{"uid": str, "game": str}]
        """
        accounts: list[GameAccount] = []

        if isinstance(raw_accounts, list):
            for ref in raw_accounts:
                if not isinstance(ref, dict):
                    continue
                uid = ref.get("uid")
                game_value = ref.get("game")
                if not uid or not game_value:
                    continue
                with contextlib.suppress(Exception):
                    accounts.append(await GameAccount.new(uid=str(uid), game=Game(str(game_value))))
            return accounts

        if isinstance(raw_accounts, dict):
            for payload in raw_accounts.values():
                if not isinstance(payload, dict):
                    continue
                with contextlib.suppress(Exception):
                    normalized = payload.copy()
                    normalized["game"] = Game(str(normalized["game"]))
                    accounts.append(GameAccount(**normalized))

        return accounts

    async def _sync_account_refs(self) -> None:
        """Persist account references in the current list schema."""
        refs = [{"uid": acc.uid, "game": acc.game.value} for acc in self.accounts]
        await DB.users.update_one({"id": self.id}, {"$set": {"accounts": refs}})

    @classmethod
    async def new(cls, user_id: int) -> UserConfig:
        if user_id in cls.cache:
            return cls.cache[user_id]

        data = await DB.users.find_one({"id": user_id})
        if data is None:
            await cls.add_empty(user_id)
            data = await DB.users.find_one({"id": user_id})

        assert data is not None

        parsed_accounts = await cls._parse_accounts(data.get("accounts", []))

        instance = UserConfig(
            id=data["id"],
            features=data["features"],
            flags=data["flags"],
            language=discord.Locale(data["language"]),
            accounts=parsed_accounts,
        )

        # Opportunistically migrate legacy object schema to list references.
        if isinstance(data.get("accounts"), dict):
            await instance._sync_account_refs()

        cls.cache[user_id] = instance
        return instance

    @classmethod
    async def add_empty(cls, user_id: int) -> None:
        await DB.users.insert_one({
            "id": user_id,
            "features": [],
            "flags": [],
            "language": "en-US",
            "accounts": []
        })

    async def _update_val(self, key: str, value: Any, operator: str = "$set") -> None:
        await DB.users.update_one({"id": self.id}, {operator: {key: value}})

        # Update the cache for direct class attributes (non-nested fields)
        if "." not in key:
            setattr(self, key, value)
    
    async def _add_account(self, game: Game, account: GameAccount) -> None:
        self.accounts.append(account)
        await DB.accounts.insert_one(account.to_dict())
        await self._sync_account_refs()
        
    async def _remove_account(self, account: GameAccount) -> None:
        self.accounts.remove(account)
        await DB.accounts.delete_one({"uid": account.uid, "game": account.game.value})
        await self._sync_account_refs()

    async def _update_language(self, locale: discord.Locale) -> None:
        await DB.users.update_one(
            {"id": self.id}, {"$set": {"language": locale.value}}
        )
        self.language = locale