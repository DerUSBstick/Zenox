"""Enka Network HTTP client with in-memory response caching."""
from __future__ import annotations

import datetime
import logging

import aiohttp

from zenox.constants import ENKA_API_URLS
from zenox.enums import Game
from zenox.exceptions import EnkaAPIError

__all__ = ("EnkaClient",)

logger = logging.getLogger(__name__)

_CACHE_TTL = datetime.timedelta(seconds=60)


class EnkaClient:
    """Thin Enka Network API client."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._cache: dict[str, tuple[dict, datetime.datetime]] = {}

    # ------------------------------------------------------------------ #
    # Cache                                                               #
    # ------------------------------------------------------------------ #

    def _cache_get(self, key: str) -> dict | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        data, ts = entry
        if datetime.datetime.now(datetime.timezone.utc) - ts < _CACHE_TTL:
            return data
        del self._cache[key]
        return None

    def _cache_set(self, key: str, data: dict) -> None:
        self._cache[key] = (data, datetime.datetime.now(datetime.timezone.utc))

    def invalidate(self, key: str) -> None:
        """Evict a cache entry by key."""
        self._cache.pop(key, None)

    # ------------------------------------------------------------------ #
    # API                                                                 #
    # ------------------------------------------------------------------ #

    async def fetch_uid(self, uid: str, game: Game) -> dict:
        """Fetch Enka data for a UID. Raises ``EnkaAPIError`` on non-200."""
        key = f"uid:{game.value}:{uid}"
        if cached := self._cache_get(key):
            return cached
        async with self._session.get(
            ENKA_API_URLS[game].format(uid=uid),
            timeout=aiohttp.ClientTimeout(total=5),
        ) as resp:
            if resp.status != 200:
                raise EnkaAPIError(status_code=resp.status)
            data = await resp.json()
        self._cache_set(key, data)
        return data

    async def fetch_profile(self, username: str) -> dict:
        """Fetch an Enka Network user profile (contains ``profile.bio``)."""
        from zenox.constants import ENKA_PROFILE_URL

        key = f"profile:{username}"
        if cached := self._cache_get(key):
            return cached
        async with self._session.get(
            ENKA_PROFILE_URL.format(username=username),
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                raise EnkaAPIError(status_code=resp.status)
            data = await resp.json()
        self._cache_set(key, data)
        return data

    async def fetch_hoyos(self, username: str) -> dict[str, dict]:
        """Fetch game accounts linked to an Enka Network profile."""
        from zenox.constants import ENKA_HOYOS_URL

        key = f"hoyos:{username}"
        if cached := self._cache_get(key):
            return cached
        async with self._session.get(
            ENKA_HOYOS_URL.format(username=username),
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status != 200:
                raise EnkaAPIError(status_code=resp.status)
            data = await resp.json()
        self._cache_set(key, data)
        return data
