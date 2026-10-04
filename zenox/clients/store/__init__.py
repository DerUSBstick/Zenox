"""Network-backed, per-game data store facade.

Usage::

    store = Store()               # no I/O yet
    await store.warm_up(session)   # fetches + caches all game data
    character = store.hsr.get_character(1001)
"""
from __future__ import annotations

import aiohttp

from .hsr import HSRStore

__all__ = ("Store",)


class Store:
    def __init__(self) -> None:
        self.hsr = HSRStore()

    async def warm_up(self, session: aiohttp.ClientSession) -> None:
        """Fetch and build the caches for every game store. Safe to call once
        during bot startup, after ``session`` has been created."""
        await self.hsr.warm_up(session)
