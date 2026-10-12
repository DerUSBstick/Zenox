"""Enka Network HTTP client with in-memory response caching."""
from __future__ import annotations

import datetime
import logging
import time

import aiohttp

from zenox.constants import ENKA_API_URLS, ENKA_HOYOS_URL, ENKA_PROFILE_URL
from zenox.enums import Game
from zenox.exceptions import EnkaAPIError
from zenox.metrics import (
    ENKA_CACHE_LOOKUPS_COUNTER,
    ENKA_HTTP_ERRORS_COUNTER,
    ENKA_REQUEST_DURATION,
    ENKA_REQUESTS_COUNTER,
)

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

    async def _request(self, endpoint: str, key: str, url: str, timeout: int) -> dict:
        """Cached GET returning JSON; records cache and request metrics."""
        if cached := self._cache_get(key):
            ENKA_CACHE_LOOKUPS_COUNTER.labels(endpoint, "hit").inc()
            return cached
        ENKA_CACHE_LOOKUPS_COUNTER.labels(endpoint, "miss").inc()

        start = time.perf_counter()
        try:
            async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                if resp.status != 200:
                    ENKA_REQUESTS_COUNTER.labels(endpoint, "http_error").inc()
                    ENKA_HTTP_ERRORS_COUNTER.labels(endpoint, str(resp.status)).inc()
                    raise EnkaAPIError(status_code=resp.status)
                data = await resp.json()
        except EnkaAPIError:
            raise
        except TimeoutError:
            ENKA_REQUESTS_COUNTER.labels(endpoint, "timeout").inc()
            raise
        except Exception:
            ENKA_REQUESTS_COUNTER.labels(endpoint, "error").inc()
            raise
        finally:
            ENKA_REQUEST_DURATION.labels(endpoint).observe(time.perf_counter() - start)

        ENKA_REQUESTS_COUNTER.labels(endpoint, "success").inc()
        self._cache_set(key, data)
        return data

    async def fetch_uid(self, uid: str, game: Game) -> dict:
        """Fetch Enka data for a UID. Raises ``EnkaAPIError`` on non-200."""
        return await self._request("uid", f"uid:{game.value}:{uid}", ENKA_API_URLS[game].format(uid=uid), 5)

    async def fetch_profile(self, username: str) -> dict:
        """Fetch an Enka Network user profile (contains ``profile.bio``)."""
        return await self._request("profile", f"profile:{username}", ENKA_PROFILE_URL.format(username=username), 10)

    async def fetch_hoyos(self, username: str) -> dict[str, dict]:
        """Fetch game accounts linked to an Enka Network profile."""
        return await self._request("hoyos", f"hoyos:{username}", ENKA_HOYOS_URL.format(username=username), 10)
