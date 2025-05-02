import sentry_sdk
import os
import io
import discord
import git
import aiohttp
import string, random, datetime
import genshin
import dotenv

from discord.utils import MISSING
from .enums import Game, GenshinCity
from.embeds import Embed
from .constants import VERSION, UTC_8
from . import emojis
from ..db.mongodb import DB
from ..l10n import LocaleStr
from sentry_sdk.integrations.loguru import LoggingLevels, LoguruIntegration
from ..static.constants import _supportCache as _cache, ZX_GAME_TO_GPY_GAME

def init_sentry() -> None:
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[
            LoguruIntegration(
                level=LoggingLevels.INFO.value, event_level=LoggingLevels.ERROR.value
            ),
        ],
        traces_sample_rate=1.0,
        enable_tracing=True,
        profiles_sample_rate=1.0,
        environment=os.environ["ENV"],
        release=VERSION,
        send_default_pii=True
    )

async def send_webhook(webhook_url, username="Zenox Logs", *, content: str=MISSING, embed: Embed=MISSING, embeds: list[Embed]=MISSING):
    if embed and embeds:
        raise ValueError("Cannot specify both `embed` and `embeds`.")
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(webhook_url, session=session)
        await webhook.send(content=content, embed=embed, embeds=embeds, username=username)

def parse_cookie(cookie: str) -> dict[str, str]:
    """Parse a cookie string into a dictionary."""
    req_cookies = {}
    for pair in cookie.split():
        key, value = pair.split("=", 1)
        req_cookies[key] = value.strip("'")
    return req_cookies


async def generate_hoyolab_token() -> None:
    """Generate Hoyolab cookies using app password"""
    cookies = await genshin.Client().login_with_password(
        account=os.getenv("HOYOLAB_EMAIL"),
        password=os.getenv("HOYOLAB_PASSWORD"),
    )
    # Update HOYOLAB_COOKIES environment variable
    env_path = '.env'
    os.environ["HOYOLAB_COOKIES"] = str(cookies)
    dotenv.set_key(env_path, "HOYOLAB_COOKIES", str(cookies))

async def redeem_code(code: str, game: Game) -> int:
    try:
        await genshin.Client(cookies=parse_cookie(os.getenv("HOYOLAB_COOKIES"))).redeem_code(
            code=code,
            game=ZX_GAME_TO_GPY_GAME[game],
            uid=None
        )
        return 1
    except genshin.errors.InvalidCookies as e:
        # Refresh cookie and try again
        await generate_hoyolab_token()
        await genshin.Client(cookies=parse_cookie(os.getenv("HOYOLAB_COOKIES"))).redeem_code(
            code=code,
            game=ZX_GAME_TO_GPY_GAME[game],
            uid=None
        )
        return 1
def ephemeral(interaction: discord.Interaction):
    return not interaction.app_permissions.embed_links

def generate_id(length=5):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def path_to_bytesio(path) -> io.BytesIO:
    with open(path, "rb") as f:
        data = f.read()
    return io.BytesIO(data)

def get_repo_version() -> str | None:
    repo = git.Repo()
    tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
    if not tags:
        return None
    return tags[-1].name

def get_now() -> datetime.datetime:
    """Get the current time in UTC+8."""
    return datetime.datetime.now(UTC_8)

def get_emoji(emoji: str):
        emoji = emoji.replace(" ", "_").replace("'", "").replace("-", "_").upper()
        """Retrieves the emoji associated with the given path.

        Args:
            path (str): The path representing the emoji (e.g., "wind", "fire").

        Returns:
            str: The corresponding emoji character, or None if not found.

        Raises:
            AttributeError: If the requested path is not found as an attribute of the class.
        """

        try:
            return getattr(emojis, emoji)  # Use getattr for dynamic attribute access
        except AttributeError:
            return ""

async def approve_request(guildid, number, client: discord.Client):
    guildid = str(guildid)
    number = int(number)
    if guildid not in _cache:
        return
        
    channel = client.get_channel(_cache[guildid]["channelID"])
    message = channel.get_partial_message(_cache[guildid]["messageID"])
    embed = Embed(
        locale=discord.Locale.american_english,
        color=0xff0000 if number != _cache[guildid]["number"] else 0x0fff00,
        title=LocaleStr(key="support_approve.invalid_number") if number != _cache[guildid]["number"] else LocaleStr(key="support_approve.success")
    )
    await message.edit(embed=embed)
    del _cache[guildid]