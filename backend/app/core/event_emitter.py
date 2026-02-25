"""Lightweight event bus — publishes events to the Redis Pub/Sub channel.

All services call ``emit_event()`` after state-changing operations.
The WebSocket manager subscribes to this channel and forwards events to
the correct connected WebSocket clients.

Never raises — fire-and-forget by design.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import structlog

_CHANNEL = "donehr:events"
log = structlog.get_logger("donehr.event_emitter")


async def emit_event(
    event_type: str,
    payload: dict,
    *,
    target_role: str | None = None,
    target_user_id: str | uuid.UUID | None = None,
) -> None:
    """
    Publish a structured event to the Redis Pub/Sub channel.

    Routing rules (applied in ConnectionManager._dispatch):
    - ``target_user_id`` set → delivered only to that user's WebSocket
    - ``target_role`` set  → delivered to all connected users with that role
      (use ``"hr_all"`` to broadcast to every HR-variant role)
    - neither set           → broadcast to every connected client

    Args:
        event_type: e.g. ``"new_application"``, ``"pipeline_stage_changed"``
        payload:    arbitrary JSON-serialisable dict
        target_role: role string or ``"hr_all"`` for all HR roles
        target_user_id: UUID of a specific recipient
    """
    try:
        from app.core.redis_client import get_redis

        redis = get_redis()
        event = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target_role": target_role,
            "target_user_id": str(target_user_id) if target_user_id else None,
        }
        await redis.publish(_CHANNEL, json.dumps(event, default=str))
    except Exception as exc:
        # Non-critical — WebSocket events must never block the main request flow
        log.debug("emit_event_failed", event_type=event_type, error=str(exc))
