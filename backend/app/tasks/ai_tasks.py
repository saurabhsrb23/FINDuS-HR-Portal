"""Celery tasks for background AI operations."""
from __future__ import annotations

import asyncio
import uuid

import structlog

from app.worker import celery_app

log = structlog.get_logger("donehr.ai_tasks")


@celery_app.task(name="ai_tasks.compute_match_score", bind=True, max_retries=2)
def compute_match_score(self, application_id: str) -> dict:
    """Compute AI match score for an application in the background."""
    async def _run():
        from app.db.session import AsyncSessionLocal
        from app.services.ai_service import get_match_score
        async with AsyncSessionLocal() as db:
            result = await get_match_score(db, uuid.UUID(application_id), force_refresh=True)
            return {"score": result.score, "grade": result.grade}

    try:
        result = asyncio.run(_run())
        log.info("match_score_computed", application_id=application_id, score=result["score"])
        return result
    except Exception as exc:
        log.error("match_score_failed", application_id=application_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="ai_tasks.rank_applicants_task", bind=True, max_retries=2)
def rank_applicants_task(self, job_id: str) -> dict:
    """Rank all applicants for a job in the background."""
    async def _run():
        from app.db.session import AsyncSessionLocal
        from app.services.ai_service import rank_applicants
        async with AsyncSessionLocal() as db:
            result = await rank_applicants(db, uuid.UUID(job_id))
            return {"job_id": job_id, "total": result.total, "ranked": len(result.ranked)}

    try:
        result = asyncio.run(_run())
        log.info("ranking_complete", job_id=job_id, total=result["total"])
        return result
    except Exception as exc:
        log.error("ranking_failed", job_id=job_id, error=str(exc))
        raise self.retry(exc=exc, countdown=120)
