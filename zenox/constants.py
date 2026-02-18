from __future__ import annotations

import discord
import datetime
import pathlib
import os

from typing import Final

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
    Game.HONKAI,
    Game.HNA,
]
REMINDERS_CONFIG_NOT_SUPPORTED: list[Game] = [
    Game.HNA,
]
YOUTUBE_NOTIFICATIONS_CONFIG_NOT_SUPPORTED: list[Game] = [

]

CODE_URLS: Final[dict[Game, str]] = {
    Game.GENSHIN: "https://hoyo-codes.seria.moe/codes?game=genshin",
    Game.STARRAIL: "https://hoyo-codes.seria.moe/codes?game=hkrpg",
    Game.ZZZ: "https://hoyo-codes.seria.moe/codes?game=nap"
}

HOYO_REDEEM_URLS: Final[dict[Game, str]] = {
    Game.GENSHIN: "https://genshin.hoyoverse.com/en/gift?code=",
    Game.STARRAIL: "https://hsr.hoyoverse.com/gift?code=",
    Game.ZZZ: "https://zenless.hoyoverse.com/redemption?code="
}

HOYO_OFFICIAL_CHANNELS: dict[Game, dict[str, str]] = {
    Game.GENSHIN: {"YouTube": "https://www.youtube.com/@GenshinImpact", "Twitch": "https://www.twitch.tv/genshinimpactofficial"},
    Game.STARRAIL: {"YouTube": "https://www.youtube.com/@HonkaiStarRail", "Twitch": "https://www.twitch.tv/honkaistarrail"},
    Game.ZZZ: {"YouTube": "https://www.youtube.com/@ZZZ_Official", "Twitch": "https://www.twitch.tv/zenlesszonezero"}
}

GAME_THUMBNAILS: dict[Game, str] = {
    Game.GENSHIN: "https://cdn.alekeagle.me/AwlF2mHD4J.webp", # Icon_Paimon_Menu.png
    Game.STARRAIL: "https://cdn.alekeagle.me/xyoBWPttHJ.webp", # Icon_Pom_Menu.png
    Game.ZZZ: "https://cdn.alekeagle.me/GBEmbiK4HG.webp" # Icon_Bangboo_Menu.png
}
"""Static Icons for redemption codes embed"""

GAME_VALUABLES: dict[Game, str] = {
    Game.GENSHIN: "Primogem",
    Game.STARRAIL: "Stellar Jade",
    Game.ZZZ: "Polychrome"
}
