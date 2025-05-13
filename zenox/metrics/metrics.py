from prometheus_client import Gauge, Counter

METRIC_PREFIX = "discord_"

CONNECTION_GAUGE = Gauge(
    METRIC_PREFIX + "connected",
    "Determines if the bot is connected to discord",
    ["shard"]
)

LATENCY_GAUGE = Gauge(
    METRIC_PREFIX + "latency",
    "Latency of the bot to discord",
    ["shard"]
)

GUILD_GAUGE = Gauge(
    METRIC_PREFIX + "guilds",
    "Number of guilds the bot is in"
)

GUILD_MEMBER_GAUGE = Gauge(
    METRIC_PREFIX + "guild_members",
    "Number of members in all guilds the bot is in"
)

CHANNEL_GAUGE = Gauge(
    METRIC_PREFIX + "channels",
    "Amount of channels the bot has access to"
)

RAM_USAGE_GAUGE = Gauge(
    METRIC_PREFIX + "ram_usage",
    "Amount of RAM the bot is using"
)

CPU_USAGE_GAUGE = Gauge(
    METRIC_PREFIX + "cpu_usage",
    "Amount of CPU the bot is using"
)

MEMORY_USAGE_GAUGE = Gauge(
    METRIC_PREFIX + "memory_usage",
    "Amount of memory the bot is using"
)

GUILD_LOCALE_GAUGE = Gauge(
    METRIC_PREFIX + "locale",
    "Locale of the guilds the bot is in",
    ["locale"]
)

UPTIME_GAUGE = Gauge(
    METRIC_PREFIX + "uptime",
    "Start time of the bot",
)