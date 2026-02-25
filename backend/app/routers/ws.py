"""WebSocket endpoints — Module 7.

Endpoints
---------
GET /ws?token=<JWT>       — main real-time event stream
GET /ws/chat?token=<JWT>  — chat stub (full implementation in Module 9)
"""
import asyncio
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.core.websocket_manager import ws_manager

log = structlog.get_logger("donehr.ws")

router = APIRouter(tags=["websocket"])


def _validate_ws_token(token: str) -> tuple[str, str] | None:
    """
    Validate a JWT access token for WebSocket auth.
    Returns (user_id, role) or None if invalid.
    Deliberately never raises — invalid tokens just reject the connection.
    """
    try:
        payload = decode_token(token)  # raises HTTPException on failure
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
    """
    Main real-time event stream.

    Protocol:
    - Client connects with ``?token=<JWT>``
    - Server immediately sends ``{event_type: "connected", payload: {user_id, role}}``
    - Server sends ``{event_type: "ping"}`` every 30 s — client should respond ``"ping"``
    - Server pushes domain events as ``{event_type, payload, timestamp}``
    - Closing with code 4001 = invalid/expired JWT
    """
    auth = _validate_ws_token(token)
    if not auth:
        # Reject the WebSocket handshake by accepting then immediately closing
        await websocket.accept()
        await websocket.close(code=4001)
        log.warning("ws_auth_failed", path="/ws")
        return

    user_id, role = auth
    await ws_manager.connect(websocket, user_id, role)

    # Start per-connection heartbeat task
    ping_task = asyncio.create_task(ws_manager.ping_loop(user_id))

    try:
        # Announce successful connection
        await websocket.send_json(
            {
                "event_type": "connected",
                "payload": {"user_id": user_id, "role": role},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Keep the connection alive; handle incoming client messages
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
    """
    Chat WebSocket — stub for Module 9.
    Currently echoes messages back to the sender.
    """
    auth = _validate_ws_token(token)
    if not auth:
        await websocket.accept()
        await websocket.close(code=4001)
        log.warning("ws_auth_failed", path="/ws/chat")
        return

    user_id, role = auth
    chat_id = f"chat:{user_id}"
    await ws_manager.connect(websocket, chat_id, role)

    try:
        await websocket.send_json(
            {
                "event_type": "chat_connected",
                "payload": {"user_id": user_id},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        while True:
            data = await websocket.receive_text()
            # Echo back (Module 9 will replace this with real chat logic)
            await websocket.send_json(
                {
                    "event_type": "chat_message",
                    "payload": {"message": data, "from": user_id},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        log.warning("ws_chat_error", user_id=user_id, error=str(exc))
    finally:
        await ws_manager.disconnect(chat_id)
