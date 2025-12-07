from __future__ import annotations

import discord
import datetime
import pathlib
import os

from zenox.enums import Game

UTC_8 = datetime.timezone(datetime.timedelta(hours=8))
SOURCE_LANG = "en-US"
L10N_PATH = pathlib.Path("./zenox/l10n")

POOL_MAX_WORKERS = min(16, (os.cpu_count() or 1))

ZENOX_LOCALES: dict[discord.Locale, dict[str, str]] = {
    discord.Locale.american_english: {"name": "English", "emoji": "🇺🇸"},
    discord.Locale.german: {"name": "Deutsch", "emoji": "🇩🇪"},
}

GAME_YOUTUBE_CHANNEL_ID: dict[Game, str] = {
    Game.GENSHIN: "UCiS882YPwZt1NfaM0gR0D9Q",
    Game.STARRAIL: "UC2PeMPA8PAOp-bynLoCeMLA",
    Game.HONKAI: "UCko6H6LokKM__B03i5_vBQQ",
    Game.ZZZ: "UC2SpC8rL9LaeQriE4YNdyzA",
    Game.HNA: "UCkkHvF8VV0YxTnDA-5dhIHg",
}

CODES_CONFIG_NOT_SUPPORTED: list[Game] = [
    Game.HNA,
]
REMINDERS_CONFIG_NOT_SUPPORTED: list[Game] = [
    Game.HNA,
]
YOUTUBE_NOTIFICATIONS_CONFIG_NOT_SUPPORTED: list[Game] = [

]