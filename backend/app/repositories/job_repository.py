"""Job repository — all DB access for the job module."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobQuestion, JobSkill, JobStatus, PipelineStage

# Default Kanban pipeline stages for every new job
_DEFAULT_STAGES = [
    ("Applied",    "#6366f1", 0),
    ("Screening",  "#f59e0b", 1),
    ("Interview",  "#3b82f6", 2),
    ("Offer",      "#10b981", 3),
    ("Hired",      "#22c55e", 4),
    ("Rejected",   "#ef4444", 5),
]


class JobRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Job CRUD ──────────────────────────────────────────────────────────────

    async def get_by_id(self, job_id: uuid.UUID) -> Job | None:
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        posted_by: uuid.UUID | None = None,
        status: JobStatus | None = None,
        job_type: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Job], int]:
        q = select(Job)
        if posted_by:
            q = q.where(Job.posted_by == posted_by)
        if status:
            q = q.where(Job.status == status)
        if job_type:
            q = q.where(Job.job_type == job_type)
        if search:
            pattern = f"%{search}%"
            q = q.where(
                sa.or_(
                    Job.title.ilike(pattern),
                    Job.department.ilike(pattern),
                    Job.location.ilike(pattern),
                )
            )
        count_q = select(func.count()).select_from(q.subquery())
        total_result = await self.db.execute(count_q)
        total = total_result.scalar_one()

        q = q.order_by(Job.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all()), total

    async def create(self, data: dict[str, Any], posted_by: uuid.UUID) -> Job:
        job = Job(**data, posted_by=posted_by)
        self.db.add(job)
        await self.db.flush()   # get job.id before creating stages
        await self._create_default_stages(job.id)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def update(self, job: Job, data: dict[str, Any]) -> Job:
        for key, value in data.items():
            setattr(job, key, value)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def delete(self, job: Job) -> None:
        await self.db.delete(job)
        await self.db.commit()

    # ── Skills ────────────────────────────────────────────────────────────────

    async def add_skill(self, job_id: uuid.UUID, skill_name: str, is_required: bool) -> JobSkill:
        skill = JobSkill(job_id=job_id, skill_name=skill_name, is_required=is_required)
        self.db.add(skill)
        await self.db.commit()
        await self.db.refresh(skill)
        return skill

    async def remove_skill(self, job_id: uuid.UUID, skill_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(JobSkill).where(JobSkill.id == skill_id, JobSkill.job_id == job_id)
        )
        skill = result.scalar_one_or_none()
        if skill is None:
            return False
        await self.db.delete(skill)
        await self.db.commit()
        return True

    # ── Questions ─────────────────────────────────────────────────────────────

    async def add_question(self, job_id: uuid.UUID, data: dict[str, Any]) -> JobQuestion:
        # Auto-assign next display_order
        result = await self.db.execute(
            select(func.coalesce(func.max(JobQuestion.display_order), -1))
            .where(JobQuestion.job_id == job_id)
        )
        max_order: int = result.scalar_one()
        data.setdefault("display_order", max_order + 1)
        question = JobQuestion(job_id=job_id, **data)
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def get_question(self, job_id: uuid.UUID, question_id: uuid.UUID) -> JobQuestion | None:
        result = await self.db.execute(
            select(JobQuestion).where(
                JobQuestion.id == question_id, JobQuestion.job_id == job_id
            )
        )
        return result.scalar_one_or_none()

    async def update_question(self, question: JobQuestion, data: dict[str, Any]) -> JobQuestion:
        for key, value in data.items():
            setattr(question, key, value)
        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def delete_question(self, question: JobQuestion) -> None:
        await self.db.delete(question)
        await self.db.commit()

    async def reorder_questions(
        self, job_id: uuid.UUID, question_ids: list[uuid.UUID]
    ) -> None:
        for order, qid in enumerate(question_ids):
            await self.db.execute(
                sa.update(JobQuestion)
                .where(JobQuestion.id == qid, JobQuestion.job_id == job_id)
                .values(display_order=order)
            )
        await self.db.commit()

    # ── Pipeline stages ───────────────────────────────────────────────────────

    async def _create_default_stages(self, job_id: uuid.UUID) -> None:
        for name, color, order in _DEFAULT_STAGES:
            stage = PipelineStage(
                job_id=job_id, stage_name=name, color=color,
                stage_order=order, is_default=True,
            )
            self.db.add(stage)

    async def add_pipeline_stage(
        self, job_id: uuid.UUID, stage_name: str, color: str
    ) -> PipelineStage:
        result = await self.db.execute(
            select(func.coalesce(func.max(PipelineStage.stage_order), -1))
            .where(PipelineStage.job_id == job_id)
        )
        max_order: int = result.scalar_one()
        stage = PipelineStage(
            job_id=job_id, stage_name=stage_name, color=color,
            stage_order=max_order + 1, is_default=False,
        )
        self.db.add(stage)
        await self.db.commit()
        await self.db.refresh(stage)
        return stage

    async def get_pipeline_stage(
        self, job_id: uuid.UUID, stage_id: uuid.UUID
    ) -> PipelineStage | None:
        result = await self.db.execute(
            select(PipelineStage).where(
                PipelineStage.id == stage_id, PipelineStage.job_id == job_id
            )
        )
        return result.scalar_one_or_none()

    async def update_pipeline_stage(
        self, stage: PipelineStage, data: dict[str, Any]
    ) -> PipelineStage:
        for key, value in data.items():
            setattr(stage, key, value)
        await self.db.commit()
        await self.db.refresh(stage)
        return stage

    async def delete_pipeline_stage(self, stage: PipelineStage) -> None:
        await self.db.delete(stage)
        await self.db.commit()

    async def reorder_pipeline(
        self, job_id: uuid.UUID, stage_orders: list[dict[str, Any]]
    ) -> None:
        for item in stage_orders:
            await self.db.execute(
                sa.update(PipelineStage)
                .where(PipelineStage.id == item["id"], PipelineStage.job_id == job_id)
                .values(stage_order=item["stage_order"])
            )
        await self.db.commit()

    # ── Analytics ─────────────────────────────────────────────────────────────

    async def get_counts_by_status(
        self, posted_by: uuid.UUID | None = None
    ) -> dict[str, int]:
        q = select(Job.status, func.count(Job.id)).group_by(Job.status)
        if posted_by:
            q = q.where(Job.posted_by == posted_by)
        result = await self.db.execute(q)
        return {str(row[0].value): int(row[1]) for row in result.all()}

    async def get_counts_by_type(
        self, posted_by: uuid.UUID | None = None
    ) -> dict[str, int]:
        q = select(Job.job_type, func.count(Job.id)).group_by(Job.job_type)
        if posted_by:
            q = q.where(Job.posted_by == posted_by)
        result = await self.db.execute(q)
        return {str(row[0].value): int(row[1]) for row in result.all()}

    async def get_total_applications(self, posted_by: uuid.UUID | None = None) -> int:
        q = select(func.coalesce(func.sum(Job.applications_count), 0))
        if posted_by:
            q = q.where(Job.posted_by == posted_by)
        result = await self.db.execute(q)
        return int(result.scalar_one())

    async def get_total_views(self, posted_by: uuid.UUID | None = None) -> int:
        q = select(func.coalesce(func.sum(Job.views_count), 0))
        if posted_by:
            q = q.where(Job.posted_by == posted_by)
        result = await self.db.execute(q)
        return int(result.scalar_one())

    async def get_top_jobs(
        self, posted_by: uuid.UUID | None = None, limit: int = 5
    ) -> list[Job]:
        q = (
            select(Job)
            .where(Job.status == JobStatus.ACTIVE)
            .order_by(Job.applications_count.desc())
            .limit(limit)
        )
        if posted_by:
            q = q.where(Job.posted_by == posted_by)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    # ── Auto-archive ──────────────────────────────────────────────────────────

    async def get_archivable_jobs(self, older_than_days: int = 90) -> list[Job]:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=older_than_days)
        result = await self.db.execute(
            select(Job).where(
                Job.status == JobStatus.CLOSED,
                Job.closed_at <= cutoff,
                Job.archived_at.is_(None),
            )
        )
        return list(result.scalars().all())

    async def bulk_set_archived(self, job_ids: list[uuid.UUID]) -> int:
        if not job_ids:
            return 0
        now = datetime.now(tz=timezone.utc)
        result = await self.db.execute(
            sa.update(Job)
            .where(Job.id.in_(job_ids))
            .values(archived_at=now)
        )
        await self.db.commit()
        return result.rowcount
