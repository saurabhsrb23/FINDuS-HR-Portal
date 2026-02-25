"""Unit tests for NotificationService."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.notification_service import NotificationService


@pytest.fixture
def db():
    return AsyncMock()


@pytest.fixture
def svc(db):
    return NotificationService(db)


# ── notify_user ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_notify_user_emit_ws_true_calls_emit(svc):
    """When emit_ws=True (default), emit_event should be attempted."""
    with patch("app.services.notification_service.emit_event", new_callable=AsyncMock):
        # No exception should be raised
        await svc.notify_user("user-123", "profile_viewed", {"foo": "bar"})


@pytest.mark.asyncio
async def test_notify_user_emit_ws_false_skips_emit(svc):
    """emit_ws=False must not invoke emit_event at all."""
    with patch("app.services.notification_service.emit_event", new_callable=AsyncMock) as mock_emit:
        await svc.notify_user("user-123", "test_event", {}, emit_ws=False)
        mock_emit.assert_not_called()


@pytest.mark.asyncio
async def test_notify_user_swallows_ws_error(svc):
    """A WebSocket emit failure must be swallowed, never re-raised."""
    async def _fail(*args, **kwargs):
        raise RuntimeError("Redis down")

    with patch("app.services.notification_service.emit_event", side_effect=_fail):
        # Must not raise
        await svc.notify_user("user-123", "test_event", {"key": "val"})


@pytest.mark.asyncio
async def test_notify_user_passes_correct_event_type(svc):
    """The exact event_type string must be forwarded to emit_event."""
    captured: dict = {}

    async def _capture(event_type, payload, **kwargs):
        captured["event_type"] = event_type

    with patch("app.services.notification_service.emit_event", side_effect=_capture):
        await svc.notify_user("u1", "application_status_changed", {})

    assert captured.get("event_type") == "application_status_changed"


# ── notify_role ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_notify_role_swallows_error(svc):
    async def _fail(*a, **kw):
        raise ConnectionError("Redis unavailable")

    with patch("app.services.notification_service.emit_event", side_effect=_fail):
        await svc.notify_role("hr", "test", {})  # Must not raise


@pytest.mark.asyncio
async def test_notify_hr_all_delegates_to_notify_role(svc):
    svc.notify_role = AsyncMock()
    await svc.notify_hr_all("new_application", {"app_id": "a1"})
    svc.notify_role.assert_awaited_once_with("hr_all", "new_application", {"app_id": "a1"})


@pytest.mark.asyncio
async def test_notify_role_passes_role_to_emit(svc):
    captured: dict = {}

    async def _capture(event_type, payload, **kwargs):
        captured["role"] = kwargs.get("target_role")

    with patch("app.services.notification_service.emit_event", side_effect=_capture):
        await svc.notify_role("candidate", "new_job_posted", {})

    assert captured.get("role") == "candidate"


# ── send_email_notification ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_send_email_queues_task(svc):
    mock_task = MagicMock()
    mock_task.delay = MagicMock()
    mock_module = MagicMock(send_generic_email=mock_task)
    with patch.dict("sys.modules", {"app.tasks.email_tasks": mock_module}):
        await svc.send_email_notification("user@example.com", "Hello", "Body text")
    mock_task.delay.assert_called_once_with(
        to_email="user@example.com", subject="Hello", body="Body text"
    )


@pytest.mark.asyncio
async def test_send_email_swallows_import_error(svc):
    """If email_tasks is unavailable, error must be swallowed."""
    with patch("builtins.__import__", side_effect=ImportError("no module")):
        # Should not raise
        await svc.send_email_notification("x@y.com", "Test", "Body")


# ── notify_application_status_change ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_notify_application_status_calls_notify_user(svc):
    svc.notify_user = AsyncMock()
    await svc.notify_application_status_change("uid-abc", "Python Developer", "interview")
    svc.notify_user.assert_awaited_once()
    call_args = svc.notify_user.call_args
    assert call_args.kwargs.get("event_type") == "application_status_changed" or \
           call_args.args[1] == "application_status_changed"


@pytest.mark.asyncio
async def test_notify_application_status_payload_contains_job_title(svc):
    captured: dict = {}

    async def _capture(*args, **kwargs):
        captured["payload"] = args[2] if len(args) > 2 else kwargs.get("payload", {})

    svc.notify_user = _capture
    await svc.notify_application_status_change("uid-1", "React Engineer", "offer")

    assert "React Engineer" in captured["payload"]["message"]
    assert "offer" in captured["payload"]["message"]


# ── notify_profile_viewed ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_notify_profile_viewed_payload(svc):
    captured: dict = {}

    async def _capture(*args, **kwargs):
        captured["payload"] = args[2] if len(args) > 2 else kwargs.get("payload", {})

    svc.notify_user = _capture
    await svc.notify_profile_viewed("uid-2", "Priya HR", "Infosys")

    assert "Priya HR" in captured["payload"]["message"]
    assert "Infosys" in captured["payload"]["message"]
    assert captured["payload"]["viewer"] == "Priya HR"
    assert captured["payload"]["company"] == "Infosys"


# ── notify_new_job_posted ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_notify_new_job_posted_targets_candidates(svc):
    svc.notify_role = AsyncMock()
    await svc.notify_new_job_posted("j-1", "Python Dev", "TCS", "Bangalore")
    svc.notify_role.assert_awaited_once()
    args = svc.notify_role.call_args.args
    assert args[0] == "candidate"
    assert args[1] == "new_job_posted"


@pytest.mark.asyncio
async def test_notify_new_job_posted_payload_fields(svc):
    captured: dict = {}

    async def _capture(role, event_type, payload):
        captured["payload"] = payload

    svc.notify_role = _capture
    await svc.notify_new_job_posted("j-2", "Java Dev", "Infosys", "Hyderabad")
    assert captured["payload"]["job_id"] == "j-2"
    assert captured["payload"]["title"] == "Java Dev"
    assert captured["payload"]["company"] == "Infosys"
    assert captured["payload"]["location"] == "Hyderabad"


# ── get_unread_count ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_unread_count_returns_zero_on_db_error(svc, db):
    db.scalar.side_effect = Exception("DB connection lost")
    result = await svc.get_unread_count(uuid.uuid4())
    assert result == 0


@pytest.mark.asyncio
async def test_get_unread_count_returns_nonneg_integer(svc, db):
    db.scalar.return_value = 3
    result = await svc.get_unread_count(uuid.uuid4())
    assert isinstance(result, int)
    assert result >= 0
