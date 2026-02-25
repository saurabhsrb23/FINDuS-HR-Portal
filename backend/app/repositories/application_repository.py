"""Application and JobAlert repository."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationAnswer, ApplicationStatus, JobAlert
from app.schemas.application import ApplyRequest, JobAlertCreate


class ApplicationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Applications ─────────────────────────────────────────────────────────

    async def get_by_id(self, app_id: uuid.UUID) -> Application | None:
        result = await self._db.execute(
            select(Application).where(Application.id == app_id)
        )
        return result.scalar_one_or_none()

    async def get_by_job_and_candidate(self, job_id: uuid.UUID, candidate_id: uuid.UUID) -> Application | None:
        result = await self._db.execute(
            select(Application).where(
                Application.job_id == job_id,
                Application.candidate_id == candidate_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_candidate(self, candidate_id: uuid.UUID) -> list[Application]:
        result = await self._db.execute(
            select(Application)
            .where(Application.candidate_id == candidate_id)
            .order_by(Application.applied_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_job(self, job_id: uuid.UUID) -> list[Application]:
        result = await self._db.execute(
            select(Application)
            .where(Application.job_id == job_id)
            .order_by(Application.applied_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        job_id: uuid.UUID,
        candidate_id: uuid.UUID,
        data: ApplyRequest,
        resume_url: str | None = None,
    ) -> Application:
        now = datetime.now(timezone.utc)
        app = Application(
            job_id=job_id,
            candidate_id=candidate_id,
            cover_letter=data.cover_letter,
            resume_url=resume_url,
            status=ApplicationStatus.APPLIED,
            timeline=[{"status": "applied", "timestamp": now.isoformat(), "note": "Application submitted"}],
        )
        self._db.add(app)
        await self._db.flush()

        # Save questionnaire answers
        for ans in data.answers:
            answer = ApplicationAnswer(
                application_id=app.id,
                question_id=ans.question_id,
                answer_text=ans.answer_text,
            )
            self._db.add(answer)

        await self._db.flush()
        await self._db.refresh(app)
        return app

    async def update_status(self, app: Application, status: ApplicationStatus, note: str | None = None) -> Application:
        now = datetime.now(timezone.utc)
        app.status = status
        timeline = list(app.timeline or [])
        timeline.append({"status": status.value, "timestamp": now.isoformat(), "note": note or ""})
        app.timeline = timeline
        await self._db.flush()
        await self._db.refresh(app)
        return app

    async def withdraw(self, app: Application) -> Application:
        return await self.update_status(app, ApplicationStatus.WITHDRAWN, "Withdrawn by candidate")

    # ── Job Alerts ───────────────────────────────────────────────────────────

    async def get_alerts_by_candidate(self, candidate_id: uuid.UUID) -> list[JobAlert]:
        result = await self._db.execute(
            select(JobAlert).where(JobAlert.candidate_id == candidate_id)
        )
        return list(result.scalars().all())

    async def get_alert_by_id(self, alert_id: uuid.UUID) -> JobAlert | None:
        result = await self._db.execute(
            select(JobAlert).where(JobAlert.id == alert_id)
        )
        return result.scalar_one_or_none()

    async def get_all_active_alerts(self) -> list[JobAlert]:
        result = await self._db.execute(
            select(JobAlert).where(JobAlert.is_active == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def create_alert(self, candidate_id: uuid.UUID, data: JobAlertCreate) -> JobAlert:
        alert = JobAlert(candidate_id=candidate_id, **data.model_dump())
        self._db.add(alert)
        await self._db.flush()
        await self._db.refresh(alert)
        return alert

    async def delete_alert(self, alert: JobAlert) -> None:
        await self._db.delete(alert)
        await self._db.flush()

    async def mark_alert_sent(self, alert: JobAlert) -> None:
        alert.last_sent_at = datetime.now(timezone.utc)
        await self._db.flush()
