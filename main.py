import os
import logging
import argparse
from zenox.config import CONFIG
from zenox.bot import Zenox
from zenox.utils import init_sentry
from zenox.enums import PrintColors


init_sentry()

parser = argparse.ArgumentParser(description="Zenox Discord Bot")
parser.add_argument("--schedule", action="store_true", default=not CONFIG.is_dev)

client = Zenox(config=CONFIG)


@client.event
async def on_ready():
    print(f"{PrintColors.OKGREEN}Logged in as {client.user}{PrintColors.ENDC}")
    await client.tree.sync()


client.run(CONFIG.discord_token, log_level=logging.INFO)
