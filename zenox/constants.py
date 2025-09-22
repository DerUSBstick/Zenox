from __future__ import annotations

import discord
import datetime
import pathlib

UTC_8 = datetime.timezone(datetime.timedelta(hours=8))
SOURCE_LANG = "en-US"
L10N_PATH = pathlib.Path("./zenox/l10n")

ZENOX_LOCALES: dict[discord.Locale, dict[str, str]] = {
    discord.Locale.american_english: {"name": "English", "emoji": "🇺🇸"},
    discord.Locale.german: {"name": "Deutsch", "emoji": "🇩🇪"}
}