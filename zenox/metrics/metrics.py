from prometheus_client import Counter, Gauge, Histogram, Summary

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
