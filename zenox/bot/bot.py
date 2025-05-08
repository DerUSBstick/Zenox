import discord
import sentry_sdk
import os
import git
from discord.ext import commands
from aiohttp import ClientSession
from loguru import logger

from pathlib import Path

from.command_tree import CommandTree
from ..db.mongodb import DB
from..static.utils import get_repo_version, get_now
from ..db.structures import Config
from ..l10n import Translator, AppCommandTranslator

class Zenox(commands.AutoShardedBot):
    owner_id: int

    def __init__(
        self,
        *,
        env: str,
        config: Config
    ) -> None:
        self.owner_id = 585834029484343298
        self.guild_id = 1129777497454686330
        self.uptime = get_now()
        self.repo = git.Repo()
        self.version = get_repo_version() or "dev"
        self.env = env
        self.config = config
        self.db = DB
        self.log_webhook_url = os.getenv(f"LOGS_WEBHOOK_{env.upper()}")

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),
            case_insensitive=True,
            help_command=None,
            tree_cls=CommandTree,
            allowed_contexts=discord.app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=False),
            allowed_installs=discord.app_commands.AppInstallationType(guild=True, user=False),
            activity=discord.CustomActivity(f"{self.version} | ZZZ Full Support")
        )

    async def setup_hook(self) -> None:
        # Set Translator
        await self.tree.set_translator(AppCommandTranslator())

        # Load Cogs
        for filepath in Path("zenox/cogs").glob("*.py"):
            cog_name = Path(filepath).stem
            try:
                await self.load_extension(f"zenox.cogs.{cog_name}")
            except Exception as e:
                print(f"Failed to load cog {cog_name!r}")
                self.capture_exception(e)
        return await super().setup_hook()
    
    def capture_exception(self, e: Exception) -> None:
        if isinstance(e, discord.NotFound) and e.code == 10062:
            return
        sentry_sdk.capture_exception(e)