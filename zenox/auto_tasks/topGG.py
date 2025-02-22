import os
import aiohttp
from typing import ClassVar
from sentry_sdk.crons import monitor
from zenox.bot.bot import Zenox
from zenox.static.utils import send_webhook

class TopGG:
    _bot: ClassVar[Zenox]
    _url = "https://top.gg/api/bots/781529450734551071/stats"

    @classmethod
    @monitor(monitor_slug='update-topgg-guild-count')
    async def execute(self, client: Zenox):
        self._bot = client
        if self._bot.env != "prod":
            return
        try:
            if token := os.getenv('TOPGG_TOKEN'):
                headers = {"Authorization": f"Bearer {token}"}
                data = {"server_count": len(client.guilds)}
                async with aiohttp.ClientSession() as sess:
                    async with sess.post(self._url, headers=headers, json=data) as response:
                        response.raise_for_status()
                        await send_webhook(client.log_webhook_url, username="TopGG Task", content="Updated Guild Count on TopGG")
        except Exception as e:
            self._bot.capture_exception(e)
            await send_webhook(client.log_webhook_url, username="TopGG Task", content="Failed to update Guild Count on TopGG")