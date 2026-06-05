from __future__ import annotations

import discord
from ..embeds import ErrorEmbed
from ..l10n import LocaleStr
from ..enums import PrintColors
from ..exceptions import ZenoxException


def get_error_embed(error: Exception, locale: discord.Locale):
    recognized = True
    embed = None

    if isinstance(error, ExceptionGroup):
        error = error.exceptions[0]
    
    if isinstance(error, ZenoxException):
        embed = ErrorEmbed(locale, title=error.title, description=error.message)

    if embed is None:
        recognized = False
        description = (
            f"{type(error).__name__}: {error}" if error else type(error).__name__
        )
        print(f"[ErrorHandler] Error - {PrintColors.FAIL}{type(error).__name__}: {error}{PrintColors.ENDC}")
        embed = ErrorEmbed(
            locale, title=LocaleStr(key="error_title"), description=description
        )

    return embed, recognized
