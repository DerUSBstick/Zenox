from itertools import product
from typing import Iterable

from prometheus_client import Counter, Gauge, Histogram

from .persistent import PersistentCounter
__all__ = (
    "initialize_series",
    "LINKED_ACCOUNTS_GAUGE",
    "SL_REQUESTS_COUNTER",
    "SL_CACHE_LOOKUPS_COUNTER",
    "SL_REQUEST_DURATION",
    "SL_HTTP_ERRORS_COUNTER",
    "SL_CHARACTER_LOOKUPS_COUNTER",
    "SL_CHARACTER_INFO_GAUGE",
    "SL_LEADERBOARD_ATTEMPTS_COUNTER",
    "SL_LEADERBOARD_FAILURES_COUNTER",
    "SL_LEADERBOARD_ERROR_GAUGE",
    "CACHE_LOOKUPS_COUNTER",
    "CACHE_ENTRIES_GAUGE",
    "CACHE_DB_DOCUMENTS_GAUGE",
    "CACHE_EVICTIONS_COUNTER",
    "ENKA_REQUESTS_COUNTER",
    "ENKA_CACHE_LOOKUPS_COUNTER",
    "ENKA_REQUEST_DURATION",
    "ENKA_HTTP_ERRORS_COUNTER",
    "LINKING_SESSIONS_COUNTER",
    "LINKING_REJECTIONS_COUNTER",
    "LINKING_ACTIVE_GAUGE",
    "LINKING_QUEUE_GAUGE",
    "CONNECTION_GAUGE",
    "LATENCY_GAUGE",
    "GUILD_GAUGE",
    "GUILD_MEMBER_GAUGE",
    "RAM_USAGE_GAUGE",
    "CPU_USAGE_GAUGE",
    "UPTIME_GAUGE",
    "GUILD_LOCALE_GAUGE",
)

METRIC_PREFIX = "discord_"

CONNECTION_GAUGE = Gauge(
    METRIC_PREFIX + "connected",
    "Determines if the bot is connected to discord.",
    ["shard"],
)

LATENCY_GAUGE = Gauge(
    METRIC_PREFIX + "latency",
    "Latency of the discord bot.",
    ["shard"],
)

GUILD_GAUGE = Gauge(
    METRIC_PREFIX + "guilds",
    "Number of guilds the bot is in.",
)

GUILD_MEMBER_GAUGE = Gauge(
    METRIC_PREFIX + "guild_members",
    "Number of members in all guilds the bot is in"
)

RAM_USAGE_GAUGE = Gauge(
    METRIC_PREFIX + "ram_usage",
    "Amount of RAM the bot is using"
)

CPU_USAGE_GAUGE = Gauge(
    METRIC_PREFIX + "cpu_usage",
    "Amount of CPU the bot is using"
)

UPTIME_GAUGE = Gauge(
    METRIC_PREFIX + "uptime",
    "Start time of the bot",
)

GUILD_LOCALE_GAUGE = Gauge(
    METRIC_PREFIX + "guild_locale",
    "Locales of guilds the bot is in",
    ["country"],
)

_DURATION_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)

SL_REQUESTS_COUNTER = Counter(
    "seeleland_requests_total",
    "Upstream Seeleland API requests.",
    ["endpoint", "outcome"],  # outcome: success|http_error|timeout|error
)

SL_CACHE_LOOKUPS_COUNTER = Counter(
    "seeleland_cache_lookups_total",
    "Seeleland cache lookups.",
    ["endpoint", "result"],  # result: hit|miss
)

SL_REQUEST_DURATION = Histogram(
    "seeleland_request_duration_seconds",
    "Duration of upstream Seeleland API requests.",
    ["endpoint"],
    buckets=_DURATION_BUCKETS,
)

SL_HTTP_ERRORS_COUNTER = Counter(
    "seeleland_http_errors_total",
    "Seeleland API HTTP error responses.",
    ["endpoint", "status"],
)

SL_CHARACTER_LOOKUPS_COUNTER = PersistentCounter(
    "seeleland_character_lookups_total",
    "Character leaderboard page lookups.",
    ["character"],
)

SL_LEADERBOARD_ERROR_GAUGE = Gauge(
    "seeleland_leaderboard_error",
    "1 while the latest fetch of a leaderboard failed; series is removed once it succeeds again.",
    ["character", "ctgr"],
)

SL_CHARACTER_INFO_GAUGE = Gauge(
    "seeleland_character_info",
    "Maps a Seeleland character ID to its display name (always 1).",
    ["character", "name"],
)

SL_LEADERBOARD_ATTEMPTS_COUNTER = PersistentCounter(
    "seeleland_leaderboard_attempts_total",
    "Discord-side leaderboard interactions.",
    ["stage"],  # stage: command|view
)

SL_LEADERBOARD_FAILURES_COUNTER = PersistentCounter(
    "seeleland_leaderboard_failures_total",
    "Discord-side leaderboard failures (API parsing, view building, interactions).",
    ["stage", "error"],  # stage: command|view|parse; error: exception class name
)

CACHE_LOOKUPS_COUNTER = Counter(
    "cache_lookups_total",
    "Generic CacheEntry lookups.",
    ["result"],  # result: memory_hit|db_hit|miss
)

CACHE_ENTRIES_GAUGE = Gauge(
    "cache_entries",
    "Number of entries in the in-memory CacheEntry cache.",
)

CACHE_DB_DOCUMENTS_GAUGE = Gauge(
    "cache_db_documents",
    "Number of documents in the persistent cache collection.",
)

CACHE_EVICTIONS_COUNTER = Counter(
    "cache_evictions_total",
    "Stale CacheEntry entries dropped on lookup.",
    ["reason"],  # reason: stale_memory|stale_db
)

ENKA_REQUESTS_COUNTER = Counter(
    "enka_requests_total",
    "Upstream Enka Network requests.",
    ["endpoint", "outcome"],  # endpoint: uid|profile|hoyos
)

ENKA_CACHE_LOOKUPS_COUNTER = Counter(
    "enka_cache_lookups_total",
    "Enka in-memory cache lookups.",
    ["endpoint", "result"],  # result: hit|miss
)

ENKA_REQUEST_DURATION = Histogram(
    "enka_request_duration_seconds",
    "Duration of upstream Enka Network requests.",
    ["endpoint"],
    buckets=_DURATION_BUCKETS,
)

ENKA_HTTP_ERRORS_COUNTER = Counter(
    "enka_http_errors_total",
    "Enka Network HTTP error responses.",
    ["endpoint", "status"],
)

LINKING_SESSIONS_COUNTER = PersistentCounter(
    "linking_sessions_total",
    "Linking session lifecycle events.",
    ["method", "event"],  # method: UID|Enka; event: started|success|expired|failed
)

LINKING_REJECTIONS_COUNTER = PersistentCounter(
    "linking_rejections_total",
    "Linking attempts rejected before a session started.",
    ["reason"],
)

LINKING_ACTIVE_GAUGE = Gauge(
    "linking_active_sessions",
    "Active linking sessions.",
)

LINKED_ACCOUNTS_GAUGE = Gauge(
    "linked_accounts",
    "Linked game accounts stored in the database.",
    ["game"],
)

LINKING_QUEUE_GAUGE = Gauge(
    "linking_queue_size",
    "Verified linking entries waiting to be finalized.",
)


def initialize_series(characters: Iterable[str], games: Iterable[str]) -> None:
    """Export known label combinations at 0 so panels show 0 instead of No data."""
    sl_endpoints = ("player", "lb", "ach")
    enka_endpoints = ("uid", "profile", "hoyos")
    outcomes = ("success", "http_error", "timeout", "error")

    for endpoint in sl_endpoints:
        SL_REQUEST_DURATION.labels(endpoint)
        for outcome in outcomes:
            SL_REQUESTS_COUNTER.labels(endpoint, outcome)
        for result in ("hit", "miss"):
            SL_CACHE_LOOKUPS_COUNTER.labels(endpoint, result)
    for endpoint in enka_endpoints:
        ENKA_REQUEST_DURATION.labels(endpoint)
        for outcome in outcomes:
            ENKA_REQUESTS_COUNTER.labels(endpoint, outcome)
        for result in ("hit", "miss"):
            ENKA_CACHE_LOOKUPS_COUNTER.labels(endpoint, result)
    for result in ("memory_hit", "db_hit", "miss"):
        CACHE_LOOKUPS_COUNTER.labels(result)
    for reason in ("stale_memory", "stale_db"):
        CACHE_EVICTIONS_COUNTER.labels(reason)

    for character in characters:
        SL_CHARACTER_LOOKUPS_COUNTER.touch(character)
    for stage in ("command", "view"):
        SL_LEADERBOARD_ATTEMPTS_COUNTER.touch(stage)
    for method, event in product(("UID", "Enka"), ("started", "success", "expired", "failed")):
        LINKING_SESSIONS_COUNTER.touch(method, event)
    for reason in ("full", "user_linking", "uid_reserved", "uid_already_linked", "linked_to_other",
                   "max_accounts", "no_accounts", "api_error", "all_linked"):
        LINKING_REJECTIONS_COUNTER.touch(reason)
    for game in games:
        LINKED_ACCOUNTS_GAUGE.labels(game).set(0)
    LINKING_ACTIVE_GAUGE.set(0)
    LINKING_QUEUE_GAUGE.set(0)