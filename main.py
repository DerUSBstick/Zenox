import os
import sys
import argparse
import discord
import logging
from loguru import logger
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv() # Load ENVs
from zenox.db.structures import Config, GuildConfig
from zenox.bot.bot import Zenox
from zenox.l10n import Translator
from zenox.static.utils import init_sentry, send_webhook

env = os.environ["ENV"]
is_dev = env == "dev"

init_sentry()

logger.add(sys.stderr, level="DEBUG" if is_dev else "INFO")
logger.add("logs/zenox.log", rotation="1 day", retention="2 weeks", level="DEBUG")

# arguments
parser = argparse.ArgumentParser()
parser.add_argument("--schedule", action="store_true", default=not is_dev)
config = Config(parser.parse_args())

client = Zenox(env=env, config=config)

@client.event
async def on_guild_join(guild: discord.Guild):
    GuildConfig(guild.id)
    embed = discord.Embed(title=f"Joined {guild.name} ({guild.id})", description=f"```\nMembers: {guild.member_count}\n```")
    await send_webhook(client.log_webhook_url, username="Guild Join Event", embed=embed)

@client.event
async def on_guild_remove(guild: discord.Guild):
    conf = GuildConfig(guild.id)
    embed = discord.Embed(title=f"Left {guild.name} ({guild.id})", description=f"```\nMembers: {guild.member_count}\n```")
    await send_webhook(client.log_webhook_url, username="Guild Leave Event", embed=embed)

@client.event
async def on_ready():
    print(f"Started in {env} Environment")
    await client.tree.sync()

client.run(os.environ[f"BOT_{env.upper()}_TOKEN"], log_level=logging.INFO)