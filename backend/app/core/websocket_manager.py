"""WebSocket connection manager with Redis Pub/Sub bridge.

Architecture
------------
* ``ConnectionManager`` is a process-level singleton (``ws_manager``).
* Each authenticated WebSocket is registered in ``active_connections``
  (keyed by ``user_id``) and in the appropriate ``role_rooms`` set.
* A background asyncio task subscribes to the Redis channel
  ``donehr:events``; for every message it calls ``_dispatch()`` to route
  the event to the correct WebSocket client(s).
* A per-connection ping task sends a heartbeat every 30 s and removes
  stale connections.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

import structlog
from fastapi import WebSocket

log = structlog.get_logger("donehr.ws_manager")

_CHANNEL = "donehr:events"
_PING_INTERVAL = 30  # seconds

# HR roles — used for the "hr_all" broadcast shorthand
_HR_ROLES = frozenset(
    ["hr", "hr_admin", "hiring_manager", "recruiter", "superadmin", "admin", "elite_admin"]
)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts events to them."""

    def __init__(self) -> None:
        # user_id (str) → WebSocket
        self.active_connections: dict[str, WebSocket] = {}
        # role (str) → set[user_id]
        self.role_rooms: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()

    # ── Connection lifecycle ──────────────────────────────────────────────────

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        role: str,
    ) -> None:
        """Accept the WebSocket and register the user."""
        await websocket.accept()
        async with self._lock:
            self.active_connections[user_id] = websocket
            self.role_rooms.setdefault(role, set()).add(user_id)
        log.info("ws_connected", user_id=user_id, role=role,
                 total=len(self.active_connections))

    async def disconnect(self, user_id: str) -> None:
        """Remove user from all rooms."""
        async with self._lock:
            self.active_connections.pop(user_id, None)
            for users in self.role_rooms.values():
                users.discard(user_id)
        log.info("ws_disconnected", user_id=user_id,
                 total=len(self.active_connections))

    # ── Broadcast helpers ─────────────────────────────────────────────────────

    async def broadcast_to_role(
        self, role: str, event_type: str, payload: dict
    ) -> None:
        """Send to all connected users with the given role."""
        user_ids = list(self.role_rooms.get(role, set()))
        for uid in user_ids:
            await self._send(uid, event_type, payload)

    async def broadcast_to_user(
        self, user_id: str, event_type: str, payload: dict
    ) -> None:
        """Send to a single user identified by user_id."""
        await self._send(user_id, event_type, payload)

    async def broadcast_to_all(self, event_type: str, payload: dict) -> None:
        """Send to every connected WebSocket."""
        for uid in list(self.active_connections.keys()):
            await self._send(uid, event_type, payload)

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _send(self, user_id: str, event_type: str, payload: dict) -> None:
        ws = self.active_connections.get(user_id)
        if not ws:
            return
        try:
            await ws.send_json(
                {
                    "event_type": event_type,
                    "payload": payload,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        except Exception:
            # Connection is dead — clean up silently
            await self.disconnect(user_id)

    # ── Redis Pub/Sub subscriber loop ─────────────────────────────────────────

    async def start_redis_subscriber(self) -> None:
        """
        Long-running background task.
        Subscribes to ``donehr:events`` and dispatches each message
        to the correct WebSocket client(s).
        Automatically reconnects on Redis failures.
        """
        from app.core.config import settings

        url = str(settings.REDIS_URL)
        log.info("ws_redis_subscriber_starting", channel=_CHANNEL)

        while True:
            r = None
            try:
                import redis.asyncio as aioredis

                r = aioredis.from_url(url, decode_responses=True)
                pubsub = r.pubsub()
                await pubsub.subscribe(_CHANNEL)
                log.info("ws_redis_subscribed", channel=_CHANNEL)

                async for raw_msg in pubsub.listen():
                    if raw_msg["type"] != "message":
                        continue
                    try:
                        event = json.loads(raw_msg["data"])
                        await self._dispatch(event)
                    except Exception as exc:
                        log.warning("ws_dispatch_error", error=str(exc))

            except asyncio.CancelledError:
                log.info("ws_redis_subscriber_cancelled")
                return

            except Exception as exc:
                log.warning("ws_redis_subscriber_error", error=str(exc))
                await asyncio.sleep(3)  # back-off before reconnect

            finally:
                if r is not None:
                    try:
                        await pubsub.unsubscribe(_CHANNEL)
                        await r.aclose()
                    except Exception:
                        pass

    async def _dispatch(self, event: dict) -> None:
        """Route an incoming Redis event to the correct WebSocket client(s)."""
        event_type: str = event.get("event_type", "")
        payload: dict = event.get("payload", {})
        target_user: str | None = event.get("target_user_id")
        target_role: str | None = event.get("target_role")

        if target_user:
            await self.broadcast_to_user(target_user, event_type, payload)
        elif target_role == "hr_all":
            # Broadcast to every HR-variant role
            for role in _HR_ROLES:
                await self.broadcast_to_role(role, event_type, payload)
        elif target_role:
            await self.broadcast_to_role(target_role, event_type, payload)
        else:
            await self.broadcast_to_all(event_type, payload)

    # ── Ping / pong heartbeat ─────────────────────────────────────────────────

    async def ping_loop(self, user_id: str) -> None:
        """
        Background task per connection.
        Sends a ``ping`` event every 30 s; disconnects if the send fails.
        """
        while user_id in self.active_connections:
            await asyncio.sleep(_PING_INTERVAL)
            ws = self.active_connections.get(user_id)
            if not ws:
                break
            try:
                await ws.send_json(
                    {
                        "event_type": "ping",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
            except Exception:
                await self.disconnect(user_id)
                break


# Process-level singleton
ws_manager = ConnectionManager()
