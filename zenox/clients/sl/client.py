from __future__ import annotations

import asyncio
import sys
import time
from typing import TYPE_CHECKING

import aiohttp

from zenox.db.classes import CacheEntry
from zenox.enums import PrintColors
from zenox.exceptions import SeelelandPageError
from zenox.metrics import (
    SL_CACHE_LOOKUPS_COUNTER,
    SL_CHARACTER_LOOKUPS_COUNTER,
    SL_HTTP_ERRORS_COUNTER,
    SL_LEADERBOARD_ERROR_GAUGE,
    SL_REQUEST_DURATION,
    SL_REQUESTS_COUNTER,
)

from .constants import SEELELAND_CACHE_TTL_SECONDS
from .models import (
    AccountData,
    AchievementLbEntry,
    # CritStats,
    LbDataEntry,
    RankingsResponse,
    SeelelandLeaderboardData,
    SeelelandResponse,
)

if TYPE_CHECKING:
    from zenox.bot.bot import Zenox


class SLClient:
    """A Client for interacting with Seeleland API"""

    def __init__(self, client: Zenox) -> None:
        self.client = client
        self.base_url = client.config.seeleland_api_url

    def _resolve_page_response(self, data: list | str) -> list | None:
        """Handle the plain-string edge cases getLbData/getAchLbData can return.

        Returns ``None`` when ``data`` is already a list (caller should proceed
        with normal parsing), or ``[]`` for the "nothing to show here" empty-page
        case. Raises ``SeelelandPageError`` for real page-bound errors.
        """
        if isinstance(data, list):
            return None
        if data == "nothing to show here":
            return []
        raise SeelelandPageError(data)

    async def _fetch_json(self, endpoint: str, path: str, description: str):
        """GET ``path`` from the Seeleland API, recording request metrics."""
        assert self.client.session is not None, "Client session is not initialized"

        start = time.perf_counter()
        try:
            response = await self.client.session.get(self.base_url + path)
            response.raise_for_status()
            data = await response.json()
        except aiohttp.ClientResponseError as exc:
            SL_REQUESTS_COUNTER.labels(endpoint, "http_error").inc()
            SL_HTTP_ERRORS_COUNTER.labels(endpoint, str(exc.status)).inc()
            raise
        except asyncio.TimeoutError:
            SL_REQUESTS_COUNTER.labels(endpoint, "timeout").inc()
            raise
        except Exception:
            SL_REQUESTS_COUNTER.labels(endpoint, "error").inc()
            raise
        finally:
            SL_REQUEST_DURATION.labels(endpoint).observe(time.perf_counter() - start)

        SL_REQUESTS_COUNTER.labels(endpoint, "success").inc()
        print(
            f"[SLClient] Info - {PrintColors.OKBLUE}Fetched {description}{PrintColors.ENDC} - "
            f"status {PrintColors.OKGREEN if response.status < 400 else PrintColors.FAIL}{response.status}{PrintColors.ENDC}"
        )
        return data

    @staticmethod
    def _log_cache(hit: bool, description: str, endpoint: str) -> None:
        SL_CACHE_LOOKUPS_COUNTER.labels(endpoint, "hit" if hit else "miss").inc()
        color = PrintColors.OKGREEN if hit else PrintColors.WARNING
        status = "HIT" if hit else "MISS"
        print(f"[SLClient] Info - {color}Cache {status}{PrintColors.ENDC} - {PrintColors.OKCYAN}{description}{PrintColors.ENDC}")

    async def get_player_data(self, uid: str, *, requested_by: int | None = None) -> SeelelandResponse:
        """Fetch player data from Seeleland API by UID"""

        cache_key = f"seeleland:player:{uid}"
        cached = await CacheEntry.get(cache_key, ttl_seconds=SEELELAND_CACHE_TTL_SECONDS)
        self._log_cache(cached is not None, f"get_player_data(uid={uid})", "player")
        if cached is not None:
            data = cached.data["payload"]
        else:
            data = await self._fetch_json("player", f"/getPlayer?uid={uid}", f"get_player_data(uid={uid})")

            await CacheEntry.set(cache_key, {"payload": data}, cached_by=requested_by or 0)

        # Extract account data (k="p") and leaderboard data from characters
        account = AccountData.from_raw(next(item for item in data if item.get("k") == "p"))

        leaderboard = {
            f"{item['k']}_{lb_key}": SeelelandLeaderboardData.from_raw(
                lb_value,
                crit_stats=None, # CritStats.from_raw(item["effstats"][lb_key]) if lb_key in item.get("effstats", {}) else None,
            )
            for item in data
            if "lb" in item and item.get("k") != "p"
            for lb_key, lb_value in item["lb"].items()
        }

        return SeelelandResponse(account=account, leaderboard=leaderboard)

    async def get_lb_data(
        self, k: str, ctgr: str, page: int, *, requested_by: int | None = None
    ) -> list[LbDataEntry]:
        """Fetch a page of a character leaderboard (``getLbData``) from the Seeleland API"""

        cache_key = f"seeleland:lb:{k}:{ctgr}:{page}"
        SL_CHARACTER_LOOKUPS_COUNTER.labels(k).inc()
        cached = await CacheEntry.get(cache_key, ttl_seconds=SEELELAND_CACHE_TTL_SECONDS)
        self._log_cache(cached is not None, f"get_lb_data(k={k}, ctgr={ctgr}, page={page})", "lb")
        if cached is not None:
            data = cached.data["payload"]
        else:
            try:
                data = await self._fetch_json(
                    "lb", f"/getLbData?k={k}&ctgr={ctgr}&page={page}", f"get_lb_data(k={k}, ctgr={ctgr}, page={page})"
                )
            except Exception:
                SL_LEADERBOARD_ERROR_GAUGE.labels(k, ctgr).set(1)
                raise

            if isinstance(data, list):
                await CacheEntry.set(cache_key, {"payload": data}, cached_by=requested_by or 0)

        try:
            resolved = self._resolve_page_response(data)
        except SeelelandPageError:
            if page == 1:
                SL_LEADERBOARD_ERROR_GAUGE.labels(k, ctgr).set(1)
            raise

        try:
            SL_LEADERBOARD_ERROR_GAUGE.remove(k, ctgr)
        except KeyError:
            pass

        if resolved is not None:
            return [LbDataEntry.from_raw(item) for item in resolved]

        return [LbDataEntry.from_raw(item) for item in data]

    async def get_ach_lb_data(self, page: int, *, requested_by: int | None = None) -> list[AchievementLbEntry]:
        """Fetch a page of the achievement leaderboard (``getAchLbData``) from the Seeleland API"""

        cache_key = f"seeleland:ach:{page}"
        cached = await CacheEntry.get(cache_key, ttl_seconds=SEELELAND_CACHE_TTL_SECONDS)
        self._log_cache(cached is not None, f"get_ach_lb_data(page={page})", "ach")
        if cached is not None:
            data = cached.data["payload"]
        else:
            data = await self._fetch_json("ach", f"/getAchLbData?page={page}", f"get_ach_lb_data(page={page})")

            if isinstance(data, list):
                await CacheEntry.set(cache_key, {"payload": data}, cached_by=requested_by or 0)

        resolved = self._resolve_page_response(data)
        if resolved is not None:
            return [AchievementLbEntry.from_raw(item) for item in resolved]

        return [AchievementLbEntry.from_raw(item) for item in data]

    async def get_rankings(
        self, k: str, ctgr: str, page: int, *, requested_by: int | None = None
    ) -> RankingsResponse:
        """Fetch a character leaderboard page, sorted ascending by rank.

        Sorting is done client-side on top of ``get_lb_data`` rather than
        relying on the API to return pre-sorted results.
        """

        entries = await self.get_lb_data(k, ctgr, page, requested_by=requested_by)

        def _rank_sort_key(entry: LbDataEntry) -> int:
            score = entry.leaderboard.get(ctgr)
            if score is None:
                return sys.maxsize
            try:
                return int(score.rank.split("/")[0])
            except ValueError:
                return sys.maxsize

        entries.sort(key=_rank_sort_key)

        return RankingsResponse(char_id=k, ctgr=ctgr, page=page, entries=entries)
