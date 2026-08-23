from __future__ import annotations

import discord
import datetime
import git
import toml
import io
import re

from typing import TYPE_CHECKING, TypeVar

from zenox.constants import UTC_8
from zenox.enums import PrintColors
from discord.utils import MISSING

if TYPE_CHECKING:
    from zenox.bot import Zenox
    from zenox.embeds import Embed

__all__ = (
    "get_now",
    "get_repo_version",
    "shorten",
    "get_project_version",
    "path_to_bytesio",
    "send_webhook",
    "split_list_to_chunks",
    "is_valid_hex_color",
    "blur_uid",
)

T = TypeVar("T")

def get_now(tz: datetime.timezone | None = None) -> datetime.datetime:
    """Get the current time in UTC+8 or the specified timezone."""
    return datetime.datetime.now(tz or UTC_8)


def get_repo_version() -> str | None:
    repo = git.Repo()
    tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime)
    if not tags:
        return None
    return tags[-1].name


def shorten(text: str, length: int) -> str:
    if len(text) > length:
        return text[:length]
    return text


def get_project_version() -> str:
    data = toml.load("pyproject.toml")
    return f"v{data['project']['version']}"


def path_to_bytesio(path) -> io.BytesIO:
    with open(path, "rb") as f:
        data = f.read()
    return io.BytesIO(data)

async def send_webhook(client: Zenox, webhook_url: str, username="Zenox Logs", *, content: str=MISSING, embed: Embed=MISSING, embeds: list[Embed]=MISSING):
    if embed and embeds:
        raise ValueError("Cannot specify both `embed` and `embeds`.")
    assert client.session is not None, "Client session is not initialized."
    print(f"[Utils] Info - {PrintColors.OKBLUE}Sending webhook to {webhook_url} with username {username}.{PrintColors.ENDC}")
    webhook = discord.Webhook.from_url(webhook_url, session=client.session)
    await webhook.send(content=content, embed=embed, embeds=embeds, username=username)
    print(f"[Utils] Info - {PrintColors.OKGREEN}Webhook sent successfully.{PrintColors.ENDC}")

def split_list_to_chunks(lst: list[T], chunk_size: int) -> list[list[T]]:
    """Split a list into chunks of a specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def is_valid_hex_color(color: str) -> bool:
    """Check if a string is a valid hex color."""
    return bool(re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", color))

def blur_uid(uid: int | str | None, *, arterisk: str = "*") -> str:
    """Blur a UID by replacing the middle digits with asterisks."""
    if uid is None:
        return ""
    uid_str = str(uid)
    middle_index = len(uid_str) // 2
    return uid_str[: middle_index - 2] + arterisk * 5 + uid_str[middle_index + 3 :]