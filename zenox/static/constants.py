import discord
import datetime
import genshin
from typing import Final, Literal
from .enums import Game, GenshinCity

_supportCache = {}

DEV_GUILD = 1129777497454686330
VERSION = 2.0
UTC_8 = datetime.timezone(datetime.timedelta(hours=8))
ZENOX_LOCALES: dict[discord.Locale, dict[str, str]] = {
    discord.Locale.american_english: {"name": "English", "emoji": "🇺🇸"},
    discord.Locale.german: {"name": "Deutsch", "emoji": "🇩🇪"}
    # discord.Locale.russian: {"name": "Russian", "emoji": "🇷🇺"}
}

LOCALE_TO_TEXTMAP: dict[discord.Locale, str] = {
    discord.Locale.american_english: "TextMapEN",
    discord.Locale.german: "TextMapDE"
}

DatabaseKey: Final[dict[Game, str]] = {
    Game.GENSHIN: "GenshinImpact",
    Game.STARRAIL: "StarRail",
    Game.ZZZ: "ZenlessZoneZero",
}

HOYOLAB_GAME_IDS: dict[Game, int] = {
    Game.GENSHIN: 2,
    Game.STARRAIL: 6,
    Game.ZZZ: 8
}
HOYOLAB_GAME_ID_TO_GAME: dict[int, Game] = {v: k for k, v in HOYOLAB_GAME_IDS.items()}

SUPPORTED_LINKING_GAMES: list[int] = [2, 6, 8]

HOYO_OFFICIAL_CHANNELS: dict[Game, dict[str, str]] = {
    Game.GENSHIN: {"YouTube": "https://www.youtube.com/@GenshinImpact", "Twitch": "https://www.twitch.tv/genshinimpactofficial"},
    Game.STARRAIL: {"YouTube": "https://www.youtube.com/@HonkaiStarRail", "Twitch": "https://www.twitch.tv/honkaistarrail"},
    Game.ZZZ: {"YouTube": "https://www.youtube.com/@ZZZ_Official", "Twitch": "https://www.twitch.tv/zenlesszonezero"}
}

HOYO_REDEEM_URLS: dict[Game, str] = {
    Game.GENSHIN: "https://genshin.hoyoverse.com/en/gift?code=",
    Game.STARRAIL: "https://hsr.hoyoverse.com/gift?code=",
    Game.ZZZ: "https://zenless.hoyoverse.com/redemption?code="
}

WIKI_PAGES: dict[Game, str | None] = {
    Game.GENSHIN: "https://genshin-impact.fandom.com/wiki/Promotional_Code",
    Game.STARRAIL: "https://honkai-star-rail.fandom.com/wiki/Redemption_Code",
    Game.ZZZ: "https://zenless-zone-zero.fandom.com/wiki/Redemption_Code"
}

GAME_TO_EMOJI: dict[Game, str] = {
    Game.GENSHIN: "<:LOGO_GENSHIN:1352032994382188614>",
    Game.STARRAIL: "<:LOGO_STARRAIL:1352033070219526187>",
    Game.ZZZ: "<:LOGO_ZENLESS:1352033174640922724>"
}

GAME_THUMBNAILS: dict[Game, str] = {
    Game.GENSHIN: "Icon_Paimon_Menu.png",
    Game.STARRAIL: "Icon_Pom_Menu.png",
    Game.ZZZ: "Icon_Bangboo_Menu.png"
}
"""Static Icons for redemption codes embed"""

LINKING_IMAGE_GUIDE: dict[Game, str] = {
    Game.GENSHIN: "https://cdn.alekeagle.me/PLNt4iCvit.png",
    Game.STARRAIL: "https://cdn.alekeagle.me/dfTz2Cqa94.png",
    Game.ZZZ: "https://cdn.alekeagle.me/FiQZh_cnxs.png"
}
"""Image guide for linking UIDs in the embed"""
HOYOLAB_LINKING_GUIDE = "https://cdn.alekeagle.me/dq3KhewfoY.png"

ZX_GAME_TO_GPY_GAME: dict[Game, genshin.Game] = {
    Game.GENSHIN: genshin.Game.GENSHIN,
    Game.STARRAIL: genshin.Game.STARRAIL,
    Game.ZZZ: genshin.Game.ZZZ
}
"""Zenox Game enum to genshin.py game enum"""

GPY_GAME_TO_ZX_GAME = {v: k for k, v in ZX_GAME_TO_GPY_GAME.items()}
"""genshin.py game enum to Zenox Game enum"""

GAME_MI18N_FILES: dict[Game, tuple[str, str]] = {
    Game.GENSHIN: ("https://fastcdn.hoyoverse.com/mi18n/bbs_oversea", "m11241040191111"),
    Game.STARRAIL: (
        "https://webstatic.hoyoverse.com/admin/mi18n/bbs_oversea",
        "m20230509hy150knmyo",
    ),
    Game.ZZZ: ("https://fastcdn.hoyoverse.com/mi18n/nap_global", "m20240410hy38foxb7k")
}
FILENAME_TO_GAME: dict[str, Game] = {v[1]: k for k, v in GAME_MI18N_FILES.items()}

LOCALE_TO_GPY_LANG = {
    discord.Locale.american_english: "en-us",
    discord.Locale.taiwan_chinese: "zh-tw",
    discord.Locale.chinese: "zh-cn",
    discord.Locale.german: "de-de",
    discord.Locale.spain_spanish: "es-es",
    discord.Locale.french: "fr-fr",
    discord.Locale.indonesian: "id-id",
    discord.Locale.italian: "it-it",
    discord.Locale.japanese: "ja-jp",
    discord.Locale.korean: "ko-kr",
    discord.Locale.brazil_portuguese: "pt-pt",
    discord.Locale.thai: "th-th",
    discord.Locale.vietnamese: "vi-vn",
    discord.Locale.turkish: "tr-tr",
    discord.Locale.russian: "ru-ru",
    discord.Locale.ukrainian: "ru-ru",
}
GPY_LANG_TO_LOCALE = {v: k for k, v in LOCALE_TO_GPY_LANG.items()}
