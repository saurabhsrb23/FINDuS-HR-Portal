"""Lightweight notification service — WebSocket events + email task dispatch."""
from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

_log = structlog.get_logger("notification_service")


class NotificationService:
    """
    Thin service that:
    1. Emits real-time WebSocket events to target users / roles
    2. Optionally dispatches Celery email tasks
    3. Provides unread chat count helper
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── WebSocket events ──────────────────────────────────────────────────────

    async def notify_user(
        self,
        user_id: str,
        event_type: str,
        payload: dict[str, Any],
        *,
        emit_ws: bool = True,
    ) -> None:
        """Send a real-time WebSocket notification to a single user."""
        if not emit_ws:
            return
        try:
            from app.core.event_emitter import emit_event
            await emit_event(event_type, payload, target_user_id=user_id)
        except Exception as exc:
            _log.warning("ws_emit_failed", event_type=event_type, user_id=user_id, error=str(exc))

    async def notify_role(
        self,
        role: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Broadcast a real-time event to all connected users with the given role."""
        try:
            from app.core.event_emitter import emit_event
            await emit_event(event_type, payload, target_role=role)
        except Exception as exc:
            _log.warning("ws_role_emit_failed", event_type=event_type, role=role, error=str(exc))

    async def notify_hr_all(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Broadcast to all HR roles (uses target_role='hr_all')."""
        await self.notify_role("hr_all", event_type, payload)

    # ── Email ────────────────────────────────────────────────────────────────

    async def send_email_notification(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> None:
        """Queue an email notification via Celery."""
        try:
            from app.tasks.email_tasks import send_generic_email
            send_generic_email.delay(to_email=to_email, subject=subject, body=body)
        except Exception as exc:
            _log.warning("email_queue_failed", to=to_email, error=str(exc))

    # ── Convenience methods ───────────────────────────────────────────────────

    async def notify_application_status_change(
        self,
        candidate_user_id: str,
        job_title: str,
        new_status: str,
    ) -> None:
        """Notify a candidate when their application status changes."""
        await self.notify_user(
            user_id=candidate_user_id,
            event_type="application_status_changed",
            payload={
                "job_title": job_title,
                "new_status": new_status,
                "message": f"Your application for '{job_title}' has been updated to {new_status}.",
            },
        )

    async def notify_profile_viewed(
        self,
        candidate_user_id: str,
        viewer_name: str,
        company_name: str,
    ) -> None:
        """Notify a candidate that an HR viewed their profile."""
        await self.notify_user(
            user_id=candidate_user_id,
            event_type="profile_viewed",
            payload={
                "viewer": viewer_name,
                "company": company_name,
                "message": f"{viewer_name} from {company_name} viewed your profile.",
            },
        )

    async def notify_new_job_posted(
        self,
        job_id: str,
        job_title: str,
        company: str,
        location: str,
    ) -> None:
        """Broadcast a new job posting event to all candidates."""
        await self.notify_role(
            role="candidate",
            event_type="new_job_posted",
            payload={
                "job_id": job_id,
                "title": job_title,
                "company": company,
                "location": location,
                "message": f"New job: {job_title} at {company} in {location}",
            },
        )

    # ── Unread count ──────────────────────────────────────────────────────────

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Return the number of unread chat messages for a user."""
        try:
            from app.models.chat import (
                ChatMessage,
                ChatMessageRead,
                ConversationParticipant,
            )

            participant_subq = (
                select(ConversationParticipant.conversation_id)
                .where(ConversationParticipant.user_id == user_id)
                .scalar_subquery()
            )
            read_ids_subq = (
                select(ChatMessageRead.message_id)
                .where(ChatMessageRead.user_id == user_id)
                .scalar_subquery()
            )
            count = await self._db.scalar(
                select(func.count())
                .select_from(ChatMessage)
                .where(
                    ChatMessage.conversation_id.in_(participant_subq),
                    ChatMessage.sender_id != user_id,
                    ChatMessage.is_deleted.is_(False),
                    ~ChatMessage.id.in_(read_ids_subq),
                )
            )
            return count or 0
        except Exception:
            return 0
