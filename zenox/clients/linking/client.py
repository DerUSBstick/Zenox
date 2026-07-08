"""Main LinkingClient – composes HoyolabClient and EnkaClient.

Usage
-----
    client = LinkingClient()
    client.start()              # call from bot.setup_hook (inside an event loop)
    ...
    await client.close()        # call from bot.close
"""
from __future__ import annotations

import logging

import aiohttp

from zenox.enums import Game

from .enka import EnkaClient
from .hoyolab import HoyolabClient

__all__ = ("LinkingClient",)

logger = logging.getLogger(__name__)


class LinkingClient:
    """Provides HoYoLAB and Enka Network API access for the linking flow."""

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None
        self._hoyolab: HoyolabClient | None = None
        self._enka: EnkaClient | None = None

    # ------------------------------------------------------------------ #
    # Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """Create the underlying ``aiohttp.ClientSession``.

        Must be called from within a running asyncio event loop
        (e.g. from ``bot.setup_hook``).
        """
        self._session = aiohttp.ClientSession()
        self._hoyolab = HoyolabClient(self._session)
        self._enka = EnkaClient(self._session)
        logger.info("[LinkingClient] HTTP session started")

    async def close(self) -> None:
        """Close the session and discard all state."""
        if self._session is not None:
            await self._session.close()
            self._session = None
        self._hoyolab = None
        self._enka = None

    # ------------------------------------------------------------------ #
    # HoYoLAB                                                             #
    # ------------------------------------------------------------------ #

    async def fetch_hoyolab_game_records(self, hoyolab_uid: str) -> list[dict]:
        assert self._hoyolab is not None
        return await self._hoyolab.fetch_game_records(hoyolab_uid)

    async def fetch_hoyolab_profile(self, hoyolab_id: str) -> dict:
        assert self._hoyolab is not None
        return await self._hoyolab.fetch_profile(hoyolab_id)

    async def ensure_hoyolab_auth(self) -> dict[str, str]:
        """Proactively ensure HoYoLAB authentication is ready.

        This is used during startup so captcha/email verification challenges
        are surfaced in the web UI immediately instead of waiting for the
        first linking request.
        """
        assert self._hoyolab is not None
        return await self._hoyolab.ensure_cookies()

    # ------------------------------------------------------------------ #
    # Enka Network                                                        #
    # ------------------------------------------------------------------ #

    async def fetch_enka(self, uid: str, game: Game) -> dict:
        assert self._enka is not None
        return await self._enka.fetch_uid(uid, game)

    async def fetch_enka_profile(self, username: str) -> dict:
        assert self._enka is not None
        return await self._enka.fetch_profile(username)

    async def fetch_enka_hoyos(self, username: str) -> dict[str, dict]:
        assert self._enka is not None
        return await self._enka.fetch_hoyos(username)

    # ------------------------------------------------------------------ #
    # Cache control (called by LinkingCacheManager)                       #
    # ------------------------------------------------------------------ #

    def invalidate_enka_profile_cache(self, username: str) -> None:
        """Evict a cached Enka profile so the next fetch is always fresh."""
        if self._enka is not None:
            self._enka.invalidate(f"profile:{username}")
