import os
import logging
from dotenv import load_dotenv
from zenox.bot import Zenox
from zenox.utils import init_sentry
from zenox.enums import PrintColors

load_dotenv()

env = os.environ["ENV"]
is_dev = env == "dev"

init_sentry()

client = Zenox(env=env)


@client.event
async def on_ready():
    print(f"{PrintColors.OKGREEN}Logged in as {client.user}{PrintColors.ENDC}")
    await client.tree.sync()


client.run(os.environ["BOT_TOKEN"], log_level=logging.INFO)
