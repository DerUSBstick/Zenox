from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from aiohttp import web

from .routes import routes

logger = logging.getLogger(__name__)

_Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]


@web.middleware
async def _cors(request: web.Request, handler: _Handler) -> web.StreamResponse:
    """Allow all origins — nginx enforces auth in front of this server."""
    if request.method == "OPTIONS":
        return web.Response(
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            }
        )
    resp = await handler(request)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


class ApiServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        self._host = host
        self._port = port
        self._runner: web.AppRunner | None = None
        self._shutdown_event: asyncio.Event | None = None

    async def start(self) -> None:
        self._shutdown_event = asyncio.Event()
        app = web.Application(middlewares=[_cors])
        app["shutdown_event"] = self._shutdown_event
        app.add_routes(routes)
        self._runner = web.AppRunner(app, access_log=None)
        await self._runner.setup()
        await web.TCPSite(self._runner, self._host, self._port).start()
        logger.info("[ApiServer] Listening on http://%s:%d", self._host, self._port)

    async def stop(self) -> None:
        if self._runner is not None:
            if self._shutdown_event is not None:
                self._shutdown_event.set()
            await self._runner.cleanup()
            self._runner = None
            self._shutdown_event = None
            logger.info("[ApiServer] Stopped")
