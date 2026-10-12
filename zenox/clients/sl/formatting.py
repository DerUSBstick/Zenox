"""Seeleland leaderboard category label formatting.

Shared between all Seeleland UI variants (the LayoutView-based
``ui/seeleland/leaderboard`` and the classic View-based
``ui/seeleland/leaderboard_classic``), so it lives here as plain domain logic
rather than inside either UI package.
"""
from __future__ import annotations

import re
from typing import NamedTuple, TYPE_CHECKING

from zenox.constants import SEELELAND_REGEX

from .constants import SEELELAND_TEAM_NAMES

if TYPE_CHECKING:
    import discord

    from zenox.clients.store.hsr import HSRStore

    from .models import CritStats

__all__ = ("CategoryKey", "format_category_label", "format_crit_stats", "parse_category_key")


class CategoryKey(NamedTuple):
    char_id: str
    bracket: str
    light_cone_id: int
    team_code: str
    speed: str | None


def parse_category_key(full_key: str) -> CategoryKey | None:
    """Parse a full ``{char_id}_{ctgr}`` leaderboard key into its parts.

    Returns ``None`` if ``full_key`` doesn't match ``SEELELAND_REGEX`` (e.g.
    the rare ``ERR``/``crayon``-prefixed templates - see the package README).
    """
    match = re.match(SEELELAND_REGEX, full_key)
    if match is None:
        return None

    char_id, bracket, lc_id, team_code, speed = match.groups()
    return CategoryKey(char_id=char_id, bracket=bracket, light_cone_id=int(lc_id), team_code=team_code or "", speed=speed)


def format_category_label(hsr: HSRStore, full_key: str, locale: discord.Locale) -> str:
    """Build a human-readable label for a Seeleland leaderboard category key.

    ``full_key`` is the full ``{char_id}_{ctgr}`` leaderboard key (matching
    ``SEELELAND_REGEX``), e.g. ``"1204_E0S5_21034TY_129"``.
    """
    match = re.match(SEELELAND_REGEX, full_key)
    if match is None:
        return full_key

    _, bracket, lc_id, team_code, speed = match.groups()

    lc_name = hsr.get_light_cone_name(int(lc_id), locale) or lc_id
    parts = [bracket, lc_name]
    if team_code:
        parts.append(SEELELAND_TEAM_NAMES.get(team_code, team_code))
    parts.append(f"Spd {speed}" if speed else "Base")

    return " · ".join(parts)


def format_crit_stats(crit_stats: CritStats | None) -> str:
    """Format Crit Rate/DMG + derived Crit Value as ``"161.8 CV (69.1/185.4)"``.

    Returns an empty string when ``crit_stats`` is ``None`` - not every
    character/build has this data available (``effstats`` is only present on
    some Seeleland leaderboard entries, see the package README).
    """
    if crit_stats is None:
        return ""
    return f"{crit_stats.cv} CV ({crit_stats.cr}/{crit_stats.cd})"
