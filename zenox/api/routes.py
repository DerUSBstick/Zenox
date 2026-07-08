"""aiohttp request handlers for the Zenox internal API."""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging

from aiohttp import web

from .challenge_store import CHALLENGES

logger = logging.getLogger(__name__)

routes = web.RouteTableDef()


@routes.get("/api/health")
async def health(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


@routes.get("/api/challenges/pending")
async def get_pending(_: web.Request) -> web.Response:
    ch = CHALLENGES.get_pending()
    return web.json_response(ch.to_dict() if ch else None)


@routes.post("/api/challenges/{id}/result")
async def post_result(request: web.Request) -> web.Response:
    challenge_id = request.match_info["id"]
    try:
        result: dict = await request.json()
    except Exception:
        raise web.HTTPBadRequest(reason="Invalid JSON body")

    if not CHALLENGES.resolve(challenge_id, result):
        raise web.HTTPNotFound(
            reason=f"Challenge {challenge_id!r} not found or already resolved"
        )
    logger.info("[API] Challenge %s resolved", challenge_id)
    return web.json_response({"ok": True})


@routes.get("/api/events")
async def sse(request: web.Request) -> web.StreamResponse:
    """Server-Sent Events — pushes challenge events to the React frontend."""
    resp = web.StreamResponse()
    resp.headers["Content-Type"] = "text/event-stream"
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"  # disable nginx proxy buffering
    await resp.prepare(request)

    queue = CHALLENGES.subscribe()
    shutdown_event = request.app.get("shutdown_event")
    try:
        # Send the current state immediately so the client is in sync on connect.
        ch = CHALLENGES.get_pending()
        if ch:
            initial = json.dumps({"type": "challenge_added", "challenge": ch.to_dict()})
        else:
            initial = json.dumps({"type": "ready"})
        await resp.write(f"data: {initial}\n\n".encode())

        while True:
            if isinstance(shutdown_event, asyncio.Event) and shutdown_event.is_set():
                break

            try:
                event = await asyncio.wait_for(queue.get(), timeout=10)
            except asyncio.TimeoutError:
                # Keepalive ping so proxies keep the stream open and we can
                # promptly detect closed transports during shutdown.
                if request.transport is None or request.transport.is_closing():
                    break
                with contextlib.suppress(ConnectionResetError, RuntimeError):
                    await resp.write(b": ping\n\n")
                continue

            await resp.write(f"data: {json.dumps(event)}\n\n".encode())
    except (ConnectionResetError, asyncio.CancelledError, RuntimeError):
        # Connection closed or request cancelled during shutdown.
        pass
    finally:
        CHALLENGES.unsubscribe(queue)
        with contextlib.suppress(ConnectionResetError, RuntimeError):
            await resp.write_eof()

    return resp
