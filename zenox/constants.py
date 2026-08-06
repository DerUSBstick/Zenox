from __future__ import annotations

import discord
import datetime
import pathlib
import os

from typing import Final

from zenox.enums import Game, Path

UTC_8 = datetime.timezone(datetime.timedelta(hours=8))
SOURCE_LANG = "en-US"
L10N_PATH = pathlib.Path("./zenox/l10n")

PATH_DISPLAY_NAMES: Final[dict[Path, str]] = {
    Path.WARRIOR: "Destruction",
    Path.ROGUE: "Hunt",
    Path.MAGE: "Erudition",
    Path.SHAMAN: "Harmony",
    Path.KNIGHT: "Preservation",
    Path.PRIEST: "Abundance",
    Path.WARLOCK: "Nihility",
    Path.MEMORY: "Remembrance",
    Path.ELATION: "Elation",
}

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
    Game.HONKAI,
    Game.HNA,
]
YOUTUBE_NOTIFICATIONS_CONFIG_NOT_SUPPORTED: list[Game] = [

]

CODE_URLS: Final[dict[Game, str]] = {
    Game.GENSHIN: "https://hoyo-codes.seria.moe/codes?game=genshin",
    Game.STARRAIL: "https://hoyo-codes.seria.moe/codes?game=hkrpg",
    Game.ZZZ: "https://hoyo-codes.seria.moe/codes?game=nap"
}

HOYOLAB_STREAM_CODES_ENDPOINT: str = "https://bbs-api-os.hoyolab.com/community/painter/wapi/circle/channel/guide/material?game_id={game_id}"

GAME_TO_ID: dict[Game, int] = {
    Game.GENSHIN: 2,
    Game.STARRAIL: 6,
    Game.ZZZ: 8,
    Game.HONKAI: 1,
    Game.HNA: 9
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
    Game.GENSHIN: "https://zipline.internal.zenox.dev/u/LUOkjT.webp", # Icon_Paimon_Menu.png
    Game.STARRAIL: "https://zipline.internal.zenox.dev/u/mIMkCT.webp", # Icon_Pom_Menu.png
    Game.ZZZ: "https://zipline.internal.zenox.dev/u/3qf3th.webp" # Icon_Bangboo_Menu.png
}
"""Static Icons for redemption codes embed"""

GAME_VALUABLES: dict[Game, str] = {
    Game.GENSHIN: "Primogem",
    Game.STARRAIL: "Stellar Jade",
    Game.ZZZ: "Polychrome"
}

ENKA_API_URLS: Final[dict[Game, str]] = {
    Game.GENSHIN: "https://enka.network/api/uid/{uid}?info",
    Game.STARRAIL: "https://enka.network/api/hsr/uid/{uid}?info",
    Game.ZZZ: "https://enka.network/api/zzz/uid/{uid}?info",
}

SIGNATURE_LOC: Final[dict[Game, list[str]]] = {
    Game.GENSHIN: ["playerInfo", "signature"],
    Game.STARRAIL: ["detailInfo", "signature"],
    Game.ZZZ: ["PlayerInfo", "SocialDetail", "Desc"]
}

NICKNAME_LOC: Final[dict[Game, list[str]]] = {
    Game.GENSHIN: ["playerInfo", "nickname"],
    Game.STARRAIL: ["detailInfo", "nickname"],
    Game.ZZZ: ["PlayerInfo", "SocialDetail", "ProfileDetail", "Nickname"]
}

# ---------------------------------------------------------------------------
# Linking
# ---------------------------------------------------------------------------

LINKING_SUPPORTED_GAMES: list[Game] = [
    Game.GENSHIN,
    Game.STARRAIL,
    Game.ZZZ,
]

HOYOLAB_GAME_ID_TO_GAME: dict[int, Game] = {
    2: Game.GENSHIN,
    6: Game.STARRAIL,
    8: Game.ZZZ,
}

# Guide images shown in the pending embed — fill in the URLs.
LINKING_IMAGE_GUIDE: dict[Game, str] = {
    Game.GENSHIN: "",
    Game.STARRAIL: "",
    Game.ZZZ: "",
}

# Enka Network profile API — used by the Enka linking method.
ENKA_PROFILE_URL: Final[str] = "https://enka.network/api/profile/{username}/"
ENKA_HOYOS_URL: Final[str] = "https://enka.network/api/profile/{username}/hoyos/"

# Maps Enka's hoyo_type field to the internal Game enum.
# 0 = Genshin Impact, 1 = Honkai: Star Rail, 2 = Zenless Zone Zero
ENKA_HOYO_TYPE_TO_GAME: Final[dict[int, Game]] = {
    0: Game.GENSHIN,
    1: Game.STARRAIL,
    2: Game.ZZZ,
}

ENKA_LINKING_GUIDE_IMAGE: str = ""
SEELELAND_REGEX = r"^(\d+)_([ES\d]+)_(\d{5})([A-Z]*)(?:_(\d+))?$"