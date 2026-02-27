from prometheus_client import Gauge
__all__ = (
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