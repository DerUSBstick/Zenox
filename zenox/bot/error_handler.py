import discord

from zenox.static.embeds import ErrorEmbed
from zenox.static.exceptions import ZenoxException
from zenox.l10n import LocaleStr

def get_error_embed(
    e: Exception,
    locale: discord.Locale,
) -> tuple[discord.Embed, bool]:
    known = True
    embed = None

    if isinstance(e, ExceptionGroup):
        e = e.exceptions[0]
    
    if isinstance(e, ZenoxException):
        embed = ErrorEmbed(locale=locale, title=e.title, description=e.message)
        

    if embed is None:
        known = False
        description = f"{type(e).__name__}: {e}" if e else type(e).__name__
        embed = ErrorEmbed(
            locale, title=LocaleStr(key="error_title"), description=description
        )
        embed.set_footer(text=LocaleStr(key="error_footer"))
    return embed, known