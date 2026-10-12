from __future__ import annotations

import git
import psutil
import discord
import sentry_sdk
import concurrent.futures
from discord.ext import commands
from aiohttp import ClientSession
from pathlib import Path
from typing import Optional

from .command_tree import CommandTree
from zenox.l10n import AppCommandTranslator
from zenox.utils import get_now, get_repo_version, LinkingCacheManager
from zenox.enums import PrintColors
from zenox.constants import POOL_MAX_WORKERS
from zenox.config import Config
from zenox.db.classes import ModuleConfig
from zenox.clients.store import Store


class Zenox(commands.AutoShardedBot):
    def __init__(self, *, config: Config) -> None:
        self.owner_id = 585834029484343298
        self.guild_id = 1129777497454686330
        self.uptime = get_now()
        self.repo = git.Repo()
        self.version = get_repo_version()
        self.env = config.env
        self.process = psutil.Process()
        self.session: Optional[ClientSession] = None
        self.config = config
        # Add Module Configurations from db/classes/config.py
        self.db_config: Optional[ModuleConfig] = None
        self.linking_cache: Optional[LinkingCacheManager] = None
        self.store = Store()

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

        if config.env == "dev":
            self.executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=POOL_MAX_WORKERS
            )
        else:
            self.executor = concurrent.futures.ProcessPoolExecutor(
                max_workers=POOL_MAX_WORKERS
            )

    async def setup_hook(self) -> None:
        self.session = ClientSession()
        try:
            await self.store.warm_up(self.session)
            print(f"[Zenox] Info - {PrintColors.OKCYAN}Store warmed up.{PrintColors.ENDC}")
        except Exception as e:
            print(f"[Zenox] Error - {PrintColors.FAIL}Failed to warm up store.{PrintColors.ENDC}")
            print(f"[Zenox] Error - {PrintColors.FAIL}{e}{PrintColors.ENDC}")
            self.capture_exception(e)

        # Start linking cache manager
        self.linking_cache = LinkingCacheManager(self)
        self.linking_cache.start()
        print(f"[Zenox] Info - {PrintColors.OKCYAN}Linking cache manager started.{PrintColors.ENDC}")

        # Load global configuration from database
        self.db_config = await ModuleConfig.new()
        print(f"[Zenox] Info - {PrintColors.OKCYAN}Loaded DB config.{PrintColors.ENDC}")

        # Set translator
        await self.tree.set_translator(AppCommandTranslator())
        print(f"[Zenox] Info - {PrintColors.OKCYAN}Translator set.{PrintColors.ENDC}")

        # Load Cogs
        for filepath in Path("zenox/cogs").glob("*.py"):
            cog_name = Path(filepath).stem
            try:
                await self.load_extension(f"zenox.cogs.{cog_name}")
                print(f"[Zenox] Info - {PrintColors.OKGREEN}Loaded cog {cog_name!r}{PrintColors.ENDC}")
            except Exception as e:
                print(f"[Zenox] Error - {PrintColors.FAIL}Failed to load cog {cog_name!r}{PrintColors.ENDC}")
                print(f"[Zenox] Error - {PrintColors.FAIL}{e}{PrintColors.ENDC}")
                self.capture_exception(e)
        return await super().setup_hook()

    async def close(self) -> None:
        print(f"[Zenox] Warning - {PrintColors.WARNING}Shutting down Zenox bot...{PrintColors.ENDC}")
        if self.linking_cache:
            await self.linking_cache.stop()
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
