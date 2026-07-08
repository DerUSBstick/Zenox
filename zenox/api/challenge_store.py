"""In-memory store for pending HoYoLAB authentication challenges.

When the bot encounters a captcha (-3101) or email-verification (-3239) response,
it registers a ``Challenge`` here and suspends login via ``wait_for_result``.
The web UI fetches pending challenges via the REST API, lets the operator solve
the widget/form, then posts the result back — at which point the suspended
coroutine resumes and login continues.

SSE listeners are notified on every add/resolve so the frontend gets push updates.
"""
from __future__ import annotations

import asyncio
import dataclasses
import uuid
from enum import Enum

__all__ = ("ChallengeStore", "Challenge", "ChallengeType", "CHALLENGES")


class ChallengeType(str, Enum):
    GEETEST_V3 = "geetest_v3"
    GEETEST_V4 = "geetest_v4"
    EMAIL_VERIFY = "email_verify"


@dataclasses.dataclass
class Challenge:
    id: str
    type: ChallengeType
    data: dict         # Geetest mmt_data; or {"description": ...} for email verify
    session_id: str    # AIGIS session_id; empty string for email verify
    _future: asyncio.Future[dict] = dataclasses.field(repr=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "session_id": self.session_id,
        }


class ChallengeStore:
    """Thread-safe (event-loop-safe) in-memory store."""

    def __init__(self) -> None:
        self._challenges: dict[str, Challenge] = {}
        self._listeners: list[asyncio.Queue[dict]] = []

    # ------------------------------------------------------------------ #
    # Mutations                                                           #
    # ------------------------------------------------------------------ #

    def add(
        self,
        *,
        challenge_type: ChallengeType,
        data: dict,
        session_id: str = "",
    ) -> Challenge:
        """Register a new pending challenge and notify SSE listeners."""
        loop = asyncio.get_running_loop()
        ch = Challenge(
            id=str(uuid.uuid4()),
            type=challenge_type,
            data=data,
            session_id=session_id,
            _future=loop.create_future(),
        )
        self._challenges[ch.id] = ch
        self._broadcast({"type": "challenge_added", "challenge": ch.to_dict()})
        return ch

    def resolve(self, challenge_id: str, result: dict) -> bool:
        """Mark a challenge as solved and wake the waiting coroutine."""
        ch = self._challenges.get(challenge_id)
        if ch is None or ch._future.done():
            return False
        ch._future.set_result(result)
        self._broadcast({"type": "challenge_resolved", "id": challenge_id})
        del self._challenges[challenge_id]
        return True

    # ------------------------------------------------------------------ #
    # Queries                                                             #
    # ------------------------------------------------------------------ #

    def get_pending(self) -> Challenge | None:
        """Return the oldest unsolved challenge, or None."""
        return next(
            (c for c in self._challenges.values() if not c._future.done()), None
        )

    # ------------------------------------------------------------------ #
    # Waiting                                                             #
    # ------------------------------------------------------------------ #

    async def wait_for_result(
        self, challenge: Challenge, *, timeout: float = 300.0
    ) -> dict | None:
        """Await the challenge result; cleans up and returns None on timeout."""
        try:
            return await asyncio.wait_for(
                asyncio.shield(challenge._future), timeout=timeout
            )
        except asyncio.TimeoutError:
            if not challenge._future.done():
                challenge._future.cancel()
            self._challenges.pop(challenge.id, None)
            return None

    # ------------------------------------------------------------------ #
    # SSE pub/sub                                                         #
    # ------------------------------------------------------------------ #

    def subscribe(self) -> asyncio.Queue[dict]:
        q: asyncio.Queue[dict] = asyncio.Queue()
        self._listeners.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict]) -> None:
        try:
            self._listeners.remove(q)
        except ValueError:
            pass

    def _broadcast(self, event: dict) -> None:
        for q in self._listeners:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass  # slow consumer — drop silently


# Module-level singleton shared by the bot and API routes.
CHALLENGES: ChallengeStore = ChallengeStore()
