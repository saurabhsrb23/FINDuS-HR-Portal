"""WebSocket endpoints — Module 7 (main) + Module 9 (chat).

Endpoints
---------
GET /ws?token=<JWT>       — main real-time event stream
GET /ws/chat?token=<JWT>  — chat WebSocket (full implementation Module 9)
"""
import asyncio
import json
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.core.websocket_manager import ws_manager

log = structlog.get_logger("donehr.ws")

router = APIRouter(tags=["websocket"])


def _validate_ws_token(token: str) -> tuple[str, str] | None:
    """Validate a JWT access token for WebSocket auth.
    Returns (user_id, role) or None if invalid.
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub", "")
        role = payload.get("role", "")
        if not user_id:
            return None
        return user_id, role
    except Exception:
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
) -> None:
    """Main real-time event stream."""
    auth = _validate_ws_token(token)
    if not auth:
        await websocket.accept()
        await websocket.close(code=4001)
        log.warning("ws_auth_failed", path="/ws")
        return

    user_id, role = auth
    await ws_manager.connect(websocket, user_id, role)
    ping_task = asyncio.create_task(ws_manager.ping_loop(user_id))

    try:
        await websocket.send_json(
            {
                "event_type": "connected",
                "payload": {"user_id": user_id, "role": role},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        while True:
            text = await websocket.receive_text()
            if text == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        log.warning("ws_error", user_id=user_id, error=str(exc))
    finally:
        ping_task.cancel()
        await ws_manager.disconnect(user_id)


@router.websocket("/ws/chat")
async def chat_websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
) -> None:
    """Chat WebSocket — full implementation (Module 9).

    Client sends JSON:
      {"type": "send", "conversation_id": "<uuid>", "content": "...", "reply_to_id": null}
      {"type": "typing", "conversation_id": "<uuid>"}
      {"type": "read", "conversation_id": "<uuid>"}
      {"type": "ping"}

    Server pushes JSON:
      {event_type: "chat_connected", payload: {user_id, role, unread}}
      {event_type: "new_message",    payload: MessageOut}
      {event_type: "message_edited", payload: MessageOut}
      {event_type: "message_deleted",payload: {message_id}}
      {event_type: "reaction_updated",payload: {message_id, reactions, added}}
      {event_type: "typing",          payload: {conversation_id, user_id, user_name}}
      {event_type: "ping"}
    """
    auth = _validate_ws_token(token)
    if not auth:
        await websocket.accept()
        await websocket.close(code=4001)
        log.warning("ws_auth_failed", path="/ws/chat")
        return

    user_id, role = auth

    from app.core.chat_manager import chat_manager

    await chat_manager.connect(websocket, user_id)

    try:
        # Send connected event with unread count
        from app.db.session import AsyncSessionLocal
        from app.repositories.chat_repository import ChatRepository
        import uuid as _uuid

        async with AsyncSessionLocal() as db:
            repo = ChatRepository(db)
            try:
                unread = await repo.get_total_unread(_uuid.UUID(user_id))
            except Exception:
                unread = 0

        await websocket.send_json(
            {
                "event_type": "chat_connected",
                "payload": {"user_id": user_id, "role": role, "unread": unread},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Process incoming messages
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                if raw == "ping":
                    await websocket.send_json(
                        {
                            "event_type": "ping",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                continue

            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json(
                    {
                        "event_type": "ping",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
            elif msg_type == "send":
                await _handle_ws_send(user_id, data)
            elif msg_type == "typing":
                await _handle_ws_typing(user_id, data)
            elif msg_type == "read":
                await _handle_ws_read(user_id, data)

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        log.warning("ws_chat_error", user_id=user_id, error=str(exc))
    finally:
        await chat_manager.disconnect(user_id)


async def _handle_ws_send(sender_id: str, data: dict) -> None:
    """Save and broadcast a new chat message."""
    from app.core.chat_manager import chat_manager
    from app.db.session import AsyncSessionLocal
    from app.schemas.chat import MessageCreate
    from app.services.chat_service import ChatService
    import uuid as _uuid
    from sqlalchemy import select

    conversation_id = data.get("conversation_id")
    content = (data.get("content") or "").strip()
    reply_to_id = data.get("reply_to_id")

    if not conversation_id or not content:
        return

    try:
        async with AsyncSessionLocal() as db:
            from app.models.user import User
            result = await db.execute(
                select(User).where(User.id == _uuid.UUID(sender_id))
            )
            user = result.scalar_one_or_none()
            if not user:
                return
            svc = ChatService(db)
            await svc.send_message(
                user,
                MessageCreate(
                    conversation_id=conversation_id,
                    content=content,
                    reply_to_id=reply_to_id,
                ),
            )
    except Exception as exc:
        log.warning("ws_send_error", sender_id=sender_id, error=str(exc))
        await chat_manager.send_to_user(sender_id, "error", {"detail": str(exc)})


async def _handle_ws_typing(sender_id: str, data: dict) -> None:
    """Broadcast typing indicator to conversation participants."""
    from app.core.chat_manager import chat_manager
    from app.db.session import AsyncSessionLocal
    from app.repositories.chat_repository import ChatRepository
    import uuid as _uuid

    conversation_id = data.get("conversation_id")
    if not conversation_id:
        return

    try:
        async with AsyncSessionLocal() as db:
            repo = ChatRepository(db)
            recipient_ids = await repo.get_participant_user_ids(
                _uuid.UUID(conversation_id)
            )
            recipient_ids = [r for r in recipient_ids if r != sender_id]
            sender = await repo.get_user(_uuid.UUID(sender_id))
            sender_name = sender.full_name if sender else "Someone"

        await chat_manager.publish_to_recipients(
            "typing",
            {
                "conversation_id": conversation_id,
                "user_id": sender_id,
                "user_name": sender_name,
            },
            recipient_ids,
        )
    except Exception as exc:
        log.debug("ws_typing_error", sender_id=sender_id, error=str(exc))


async def _handle_ws_read(user_id: str, data: dict) -> None:
    """Mark conversation messages as read."""
    from app.db.session import AsyncSessionLocal
    from app.services.chat_service import ChatService
    import uuid as _uuid
    from sqlalchemy import select

    conversation_id = data.get("conversation_id")
    if not conversation_id:
        return

    try:
        async with AsyncSessionLocal() as db:
            from app.models.user import User
            result = await db.execute(
                select(User).where(User.id == _uuid.UUID(user_id))
            )
            user = result.scalar_one_or_none()
            if not user:
                return
            svc = ChatService(db)
            await svc.mark_read(user, conversation_id)
    except Exception as exc:
        log.debug("ws_read_error", user_id=user_id, error=str(exc))
