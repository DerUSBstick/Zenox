from __future__ import annotations

import discord
from ..embeds import ErrorEmbed
from ..l10n import LocaleStr


def get_error_embed(error: Exception, locale: discord.Locale):
    recognized = True
    embed = None

    if isinstance(error, ExceptionGroup):
        error = error.exceptions[0]

    if embed is None:
        recognized = False
        description = (
            f"{type(error).__name__}: {error}" if error else type(error).__name__
        )

        embed = ErrorEmbed(
            locale, title=LocaleStr(key="error_title"), description=description
        )

    return embed, recognized
