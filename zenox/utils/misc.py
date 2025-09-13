from __future__ import annotations

import datetime
import git
import toml

from zenox.constants import UTC_8

__all__ = ("get_now", "get_repo_version", "shorten")


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
