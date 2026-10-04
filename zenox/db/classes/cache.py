from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, ClassVar, Dict

from ..mongodb import DB

__all__ = ("CacheEntry",)


@dataclass
class CacheEntry:
    """A small, generic two-tier cache primitive.

    Backed by an in-memory dict (fast, process-local) with `DB.cache` (MongoDB)
    as a persistent fallback so cached data survives bot restarts. Freshness is
    decided by the caller via ``ttl_seconds`` - a bare timestamp alone doesn't
    imply an expiry, since different data types want different lifetimes.
    """

    identifier: str
    cached_by: int
    data: Dict[str, Any]
    timestamp: int

    cache: ClassVar[Dict[str, CacheEntry]] = {}

    @classmethod
    def _is_fresh(cls, timestamp: int, ttl_seconds: int) -> bool:
        return time.time() - timestamp < ttl_seconds

    @classmethod
    async def get(cls, identifier: str, *, ttl_seconds: int) -> CacheEntry | None:
        """Fetch a cache entry by identifier, or ``None`` if missing/stale."""
        entry = cls.cache.get(identifier)
        if entry is not None:
            if cls._is_fresh(entry.timestamp, ttl_seconds):
                return entry
            del cls.cache[identifier]

        data = await DB.cache.find_one({"identifier": identifier})
        if data is None:
            return None

        entry = cls(
            identifier=data["identifier"],
            cached_by=data["cached_by"],
            data=data["data"],
            timestamp=data["timestamp"],
        )
        if not cls._is_fresh(entry.timestamp, ttl_seconds):
            return None

        cls.cache[identifier] = entry
        return entry

    @classmethod
    async def set(cls, identifier: str, data: Dict[str, Any], *, cached_by: int) -> CacheEntry:
        """Store (upsert) a cache entry, updating both the DB and in-memory cache."""
        timestamp = int(time.time())
        entry = cls(identifier=identifier, cached_by=cached_by, data=data, timestamp=timestamp)

        await DB.cache.update_one(
            {"identifier": identifier},
            {"$set": {"cached_by": cached_by, "data": data, "timestamp": timestamp}},
            upsert=True,
        )
        cls.cache[identifier] = entry
        return entry
