"""Celery tasks for job management (auto-archive, deadline enforcement)."""
from __future__ import annotations

import structlog

from app.worker import celery_app

log = structlog.get_logger("donehr.job_tasks")


@celery_app.task(name="job_tasks.auto_archive_expired_jobs", bind=True, max_retries=3)
def auto_archive_expired_jobs(self) -> dict:  # type: ignore[override]
    """
    Archive jobs that have been closed/inactive for more than 90 days.
    Runs daily via Celery Beat.
    """
    import asyncio

    return asyncio.run(_auto_archive_expired_jobs_async())


async def _auto_archive_expired_jobs_async() -> dict:
    from app.db.session import AsyncSessionLocal
    from app.repositories.job_repository import JobRepository

    async with AsyncSessionLocal() as db:
        repo = JobRepository(db)
        jobs = await repo.get_archivable_jobs(days_old=90)
        if not jobs:
            log.info("auto_archive.no_jobs_to_archive")
            return {"archived": 0}

        ids = [j.id for j in jobs]
        await repo.bulk_set_archived(ids)
        await db.commit()

        log.info("auto_archive.done", count=len(ids))
        return {"archived": len(ids)}


@celery_app.task(name="job_tasks.close_deadline_passed_jobs", bind=True, max_retries=3)
def close_deadline_passed_jobs(self) -> dict:  # type: ignore[override]
    """
    Close active jobs whose deadline has passed.
    Runs every hour via Celery Beat.
    """
    import asyncio

    return asyncio.run(_close_deadline_passed_jobs_async())


async def _close_deadline_passed_jobs_async() -> dict:
    from datetime import datetime, timezone

    from sqlalchemy import select, update

    from app.db.session import AsyncSessionLocal
    from app.models.job import Job, JobStatus

    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        stmt = (
            update(Job)
            .where(
                Job.status == JobStatus.ACTIVE,
                Job.deadline.isnot(None),
                Job.deadline < now,
            )
            .values(status=JobStatus.CLOSED, closed_at=now)
        )
        result = await db.execute(stmt)
        await db.commit()

        count = result.rowcount
        log.info("deadline_close.done", count=count)
        return {"closed": count}
