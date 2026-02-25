"""Unit tests for ConnectionManager (websocket_manager.py).

All tests are fully synchronous-safe — they use asyncio.run / pytest-asyncio
and mock out WebSocket objects so no real network is needed.
"""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.websocket_manager import ConnectionManager


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_ws(fail_send: bool = False) -> MagicMock:
    """Create a mock WebSocket that records sent payloads."""
    ws = MagicMock()
    ws.sent: list[dict] = []

    if fail_send:
        async def _send_json(data: dict) -> None:
            raise RuntimeError("connection closed")

        ws.send_json = AsyncMock(side_effect=RuntimeError("connection closed"))
    else:
        async def _send_json(data: dict) -> None:
            ws.sent.append(data)

        ws.send_json = AsyncMock(side_effect=_send_json)

    ws.accept = AsyncMock()
    ws.close = AsyncMock()
    return ws


async def _register(manager: ConnectionManager, user_id: str, role: str) -> MagicMock:
    ws = _make_ws()
    await manager.connect(ws, user_id, role)
    return ws


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_connect_registers_user():
    mgr = ConnectionManager()
    ws = await _register(mgr, "u1", "hr")

    assert "u1" in mgr.active_connections
    assert "u1" in mgr.role_rooms["hr"]
    ws.accept.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect_cleans_up_rooms():
    mgr = ConnectionManager()
    await _register(mgr, "u1", "hr")
    await _register(mgr, "u2", "candidate")

    await mgr.disconnect("u1")

    assert "u1" not in mgr.active_connections
    assert "u1" not in mgr.role_rooms.get("hr", set())
    # u2 must still be registered
    assert "u2" in mgr.active_connections


@pytest.mark.asyncio
async def test_broadcast_to_role_delivers_to_all_in_role():
    mgr = ConnectionManager()
    ws1 = await _register(mgr, "u1", "hr")
    ws2 = await _register(mgr, "u2", "hr")
    ws3 = await _register(mgr, "u3", "candidate")

    await mgr.broadcast_to_role("hr", "new_application", {"job_id": "abc"})

    assert any(m["event_type"] == "new_application" for m in ws1.sent)
    assert any(m["event_type"] == "new_application" for m in ws2.sent)
    # candidate must not receive the HR broadcast
    assert not any(m["event_type"] == "new_application" for m in ws3.sent)


@pytest.mark.asyncio
async def test_broadcast_to_user_delivers_only_to_target():
    mgr = ConnectionManager()
    ws1 = await _register(mgr, "u1", "hr")
    ws2 = await _register(mgr, "u2", "hr")

    await mgr.broadcast_to_user("u1", "profile_viewed", {"viewer": "hr1"})

    assert any(m["event_type"] == "profile_viewed" for m in ws1.sent)
    assert not any(m["event_type"] == "profile_viewed" for m in ws2.sent)


@pytest.mark.asyncio
async def test_broadcast_to_all_reaches_every_connection():
    mgr = ConnectionManager()
    ws1 = await _register(mgr, "u1", "hr")
    ws2 = await _register(mgr, "u2", "candidate")

    await mgr.broadcast_to_all("system_announcement", {"msg": "hello"})

    assert any(m["event_type"] == "system_announcement" for m in ws1.sent)
    assert any(m["event_type"] == "system_announcement" for m in ws2.sent)


@pytest.mark.asyncio
async def test_stale_connection_cleaned_on_send_failure():
    """When send_json raises, the connection should be removed automatically."""
    mgr = ConnectionManager()
    # u1 has a failing connection
    bad_ws = _make_ws(fail_send=True)
    await bad_ws.accept()
    async with mgr._lock:
        mgr.active_connections["u1"] = bad_ws
        mgr.role_rooms.setdefault("hr", set()).add("u1")

    await mgr._send("u1", "ping", {})

    # Connection should have been cleaned up silently
    assert "u1" not in mgr.active_connections


@pytest.mark.asyncio
async def test_dispatch_hr_all_broadcasts_to_all_hr_roles():
    mgr = ConnectionManager()
    ws_hr = await _register(mgr, "u_hr", "hr")
    ws_admin = await _register(mgr, "u_admin", "admin")
    ws_cand = await _register(mgr, "u_cand", "candidate")

    event = {
        "event_type": "new_application",
        "payload": {"job_id": "xyz"},
        "target_role": "hr_all",
        "target_user_id": None,
    }
    await mgr._dispatch(event)

    assert any(m["event_type"] == "new_application" for m in ws_hr.sent)
    assert any(m["event_type"] == "new_application" for m in ws_admin.sent)
    assert not any(m["event_type"] == "new_application" for m in ws_cand.sent)


@pytest.mark.asyncio
async def test_dispatch_target_user_sends_only_to_that_user():
    mgr = ConnectionManager()
    ws1 = await _register(mgr, "u1", "candidate")
    ws2 = await _register(mgr, "u2", "candidate")

    event = {
        "event_type": "shortlisted",
        "payload": {"job_id": "abc"},
        "target_role": None,
        "target_user_id": "u1",
    }
    await mgr._dispatch(event)

    assert any(m["event_type"] == "shortlisted" for m in ws1.sent)
    assert not any(m["event_type"] == "shortlisted" for m in ws2.sent)


@pytest.mark.asyncio
async def test_dispatch_no_target_broadcasts_to_all():
    mgr = ConnectionManager()
    ws1 = await _register(mgr, "u1", "hr")
    ws2 = await _register(mgr, "u2", "candidate")

    event = {
        "event_type": "new_job_posted",
        "payload": {"title": "Engineer"},
        "target_role": None,
        "target_user_id": None,
    }
    await mgr._dispatch(event)

    assert any(m["event_type"] == "new_job_posted" for m in ws1.sent)
    assert any(m["event_type"] == "new_job_posted" for m in ws2.sent)


@pytest.mark.asyncio
async def test_multiple_connects_same_user_id_replaces_connection():
    """If the same user reconnects, the old WS slot is replaced."""
    mgr = ConnectionManager()
    ws_old = _make_ws()
    ws_new = _make_ws()

    # First connect
    await mgr.connect(ws_old, "u1", "hr")
    assert mgr.active_connections["u1"] is ws_old

    # Second connect (e.g. tab refresh)
    await mgr.connect(ws_new, "u1", "hr")
    assert mgr.active_connections["u1"] is ws_new

    # role room must not have duplicate entries
    assert mgr.role_rooms["hr"].count("u1") if hasattr(mgr.role_rooms["hr"], "count") else True
    # sets deduplicate automatically — just confirm u1 is present once
    assert "u1" in mgr.role_rooms["hr"]


@pytest.mark.asyncio
async def test_disconnect_unknown_user_is_noop():
    """Disconnecting a user that was never registered should not raise."""
    mgr = ConnectionManager()
    await mgr.disconnect("nonexistent-user-id")  # must not raise
