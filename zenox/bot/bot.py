from __future__ import annotations

import git
import psutil
import discord
import sentry_sdk
import os
from discord.ext import commands
from aiohttp import ClientSession
from pathlib import Path
from typing import Optional

from .command_tree import CommandTree
from ..l10n import AppCommandTranslator
from ..utils import get_now, get_repo_version
from ..enums import PrintColors


class Zenox(commands.AutoShardedBot):
    def __init__(self, *, env: str) -> None:
        self.owner_id = 585834029484343298
        self.guild_id = 1129777497454686330
        self.uptime = get_now()
        self.repo = git.Repo()
        self.version = get_repo_version()
        self.env = env
        self.process = psutil.Process()
        self.session: Optional[ClientSession] = None
        self.webhook_url: str | None = os.getenv("DISCORD_WEBHOOK")

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),
            case_insensitive=True,
            help_command=None,
            tree_cls=CommandTree,
            allowed_contexts=discord.app_commands.AppCommandContext(
                guild=True, dm_channel=False, private_channel=False
            ),
            allowed_installs=discord.app_commands.AppInstallationType(
                guild=True, user=False
            ),
            activity=discord.CustomActivity(f"{self.version} | Zenox"),
        )

    async def setup_hook(self) -> None:
        self.session = ClientSession()

        # Set translator
        await self.tree.set_translator(AppCommandTranslator())

        # Load Cogs
        for filepath in Path("zenox/cogs").glob("*.py"):
            cog_name = Path(filepath).stem
            try:
                await self.load_extension(f"zenox.cogs.{cog_name}")
                print(f"{PrintColors.OKGREEN}Loaded cog {cog_name!r}{PrintColors.ENDC}")
            except Exception as e:
                print(
                    f"{PrintColors.FAIL}Failed to load cog {cog_name!r}{PrintColors.ENDC}"
                )
                self.capture_exception(e)
        return await super().setup_hook()

    async def close(self) -> None:
        if self.session:
            await self.session.close()
        return await super().close()

    def capture_exception(self, error: Exception) -> None:
        if isinstance(error, discord.NotFound) and error.code == 10062:
            return
        sentry_sdk.capture_exception(error)

    @property
    def ram_usage(self) -> float:
        return self.process.memory_info().rss / 1024**2
