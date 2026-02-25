"""Celery tasks for job alerts — daily email digest at 07:00 UTC."""
from __future__ import annotations

import asyncio

import structlog

from app.worker import celery_app

log = structlog.get_logger("donehr.job_alert_tasks")


async def _send_alerts_async() -> int:
    """Fetch active job alerts and send email digests."""
    from sqlalchemy import or_, select

    from app.db.session import AsyncSessionLocal
    from app.models.application import JobAlert
    from app.models.job import Job, JobStatus
    from app.tasks.email_tasks import send_job_alert_email

    sent = 0
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(JobAlert).where(JobAlert.is_active == True)  # noqa: E712
        )
        alerts = list(result.scalars().all())

        for alert in alerts:
            # Find matching jobs
            stmt = select(Job).where(Job.status == JobStatus.ACTIVE)
            conditions = []
            if alert.keywords:
                for kw in alert.keywords.split(","):
                    kw = kw.strip()
                    if kw:
                        conditions.append(Job.title.ilike(f"%{kw}%"))
                        conditions.append(Job.description.ilike(f"%{kw}%"))
            if alert.location:
                conditions.append(Job.location.ilike(f"%{alert.location}%"))
            if alert.job_type:
                conditions.append(Job.job_type == alert.job_type)
            if alert.salary_min:
                conditions.append(Job.salary_max >= alert.salary_min)

            if conditions:
                stmt = stmt.where(or_(*conditions))

            stmt = stmt.order_by(Job.created_at.desc()).limit(10)
            job_result = await db.execute(stmt)
            jobs = list(job_result.scalars().all())

            if jobs:
                # Get candidate email
                from app.models.candidate import CandidateProfile
                from app.models.user import User
                profile_result = await db.execute(
                    select(CandidateProfile).where(CandidateProfile.id == alert.candidate_id)
                )
                profile = profile_result.scalar_one_or_none()
                if not profile:
                    continue

                user_result = await db.execute(
                    select(User).where(User.id == profile.user_id)
                )
                user = user_result.scalar_one_or_none()
                if not user:
                    continue

                # Queue email task
                job_list = [{"title": j.title, "company": j.company_name or "", "location": j.location or ""} for j in jobs]
                send_job_alert_email.delay(user.email, alert.title, job_list)

                # Mark sent
                from datetime import datetime, timezone
                alert.last_sent_at = datetime.now(timezone.utc)
                sent += 1

        await db.commit()

    return sent


@celery_app.task(name="job_alert_tasks.send_job_alerts", bind=True, max_retries=2)
def send_job_alerts(self) -> str:
    """Send daily job alert digests to candidates."""
    try:
        sent = asyncio.run(_send_alerts_async())
        log.info("job_alerts_sent", count=sent)
        return f"Sent {sent} job alert digest(s)"
    except Exception as exc:
        log.error("job_alerts_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300)
