"""Chat WebSocket connection manager with Redis Pub/Sub — Module 9."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

import structlog
from fastapi import WebSocket

log = structlog.get_logger("donehr.chat_manager")

_CHAT_CHANNEL = "donehr:chat"


class ChatConnectionManager:
    """Manages chat WebSocket connections separately from the main event stream."""

    def __init__(self) -> None:
        self.connections: dict[str, WebSocket] = {}  # user_id -> WebSocket
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            self.connections[user_id] = websocket
        log.info("chat_connected", user_id=user_id, total=len(self.connections))

    async def disconnect(self, user_id: str) -> None:
        async with self._lock:
            self.connections.pop(user_id, None)
        log.info("chat_disconnected", user_id=user_id, total=len(self.connections))

    def is_connected(self, user_id: str) -> bool:
        return user_id in self.connections

    async def send_to_user(self, user_id: str, event_type: str, payload: dict) -> None:
        ws = self.connections.get(user_id)
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
            await self.disconnect(user_id)

    async def publish_to_recipients(
        self,
        event_type: str,
        payload: dict,
        recipient_ids: list[str],
    ) -> None:
        """Publish a chat event to Redis → distributed delivery; fallback in-process."""
        try:
            from app.core.redis_client import get_redis

            redis = get_redis()
            event = {
                "event_type": event_type,
                "payload": payload,
                "recipients": recipient_ids,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await redis.publish(_CHAT_CHANNEL, json.dumps(event, default=str))
        except Exception as exc:
            log.debug("chat_publish_failed", event_type=event_type, error=str(exc))
            # Fallback: direct in-process delivery
            for uid in recipient_ids:
                await self.send_to_user(uid, event_type, payload)

    async def start_chat_subscriber(self) -> None:
        """Subscribe to donehr:chat Redis channel and deliver to connected clients."""
        from app.core.config import settings

        url = str(settings.REDIS_URL)
        log.info("chat_redis_subscriber_starting", channel=_CHAT_CHANNEL)

        while True:
            r = None
            try:
                import redis.asyncio as aioredis

                r = aioredis.from_url(url, decode_responses=True)
                pubsub = r.pubsub()
                await pubsub.subscribe(_CHAT_CHANNEL)
                log.info("chat_redis_subscribed", channel=_CHAT_CHANNEL)

                async for raw_msg in pubsub.listen():
                    if raw_msg["type"] != "message":
                        continue
                    try:
                        event = json.loads(raw_msg["data"])
                        event_type: str = event.get("event_type", "")
                        payload: dict = event.get("payload", {})
                        recipients: list[str] = event.get("recipients", [])
                        for uid in recipients:
                            await self.send_to_user(uid, event_type, payload)
                    except Exception as exc:
                        log.warning("chat_dispatch_error", error=str(exc))

            except asyncio.CancelledError:
                log.info("chat_redis_subscriber_cancelled")
                return
            except Exception as exc:
                log.warning("chat_redis_subscriber_error", error=str(exc))
                await asyncio.sleep(3)
            finally:
                if r is not None:
                    try:
                        await pubsub.unsubscribe(_CHAT_CHANNEL)
                        await r.aclose()
                    except Exception:
                        pass


chat_manager = ChatConnectionManager()
