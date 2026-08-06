"""Base class for network-backed, disk-cache-fallback game data stores."""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import ClassVar

import aiohttp
import discord

from zenox.exceptions import EnkaAPIError

__all__ = ("GameStore",)

logger = logging.getLogger(__name__)


class GameStore:
    """Base class for a single game's data store.

    Subclasses fetch their raw JSON files from ``BASE_URL`` and are responsible
    for building typed accessors on top of the raw data. Every successfully
    fetched file is cached on disk under ``CACHE_DIR`` so that a temporary
    outage of the remote API can fall back to the last known-good copy.
    """

    BASE_URL: ClassVar[str]
    CACHE_DIR: ClassVar[Path]
    TEXT_MAP_FILE: ClassVar[str]

    def __init__(self) -> None:
        self._raw: dict[str, dict] = {}

    async def _fetch_json(self, session: aiohttp.ClientSession, filename: str) -> dict:
        """Fetch a JSON file from ``BASE_URL``, caching it on disk on success and
        falling back to the on-disk cache if the request fails."""
        url = f"{self.BASE_URL}{filename}"
        cache_path = self.CACHE_DIR / filename

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    raise EnkaAPIError(status_code=resp.status)
                data = await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError, EnkaAPIError) as e:
            if cache_path.is_file():
                logger.warning(
                    "Failed to fetch %r (%s), falling back to on-disk cache at %s.",
                    url, e, cache_path,
                )
                with cache_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                status_code = e.status_code if isinstance(e, EnkaAPIError) else None
                raise EnkaAPIError(status_code=status_code) from e
        else:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with cache_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)

        self._raw[filename] = data
        return data

    def get_loc(self, loc: str, lang: discord.Locale) -> str:
        """Resolve a localized string from the store's text map file."""
        file = self._raw.get(self.TEXT_MAP_FILE, {})

        source = file.get("en", {}).get(loc)
        localized = file.get(lang.language_code, {}).get(loc)

        if not (source or localized):
            raise ValueError(
                f"Localization for '{loc}' not found in store for language "
                f"'{lang.language_code}' or source language 'en'."
            )

        return localized if localized else source
