"""Job service — business logic for the job posting module."""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import JobStatus
from app.models.user import UserRole
from app.repositories.job_repository import JobRepository
from app.schemas.job import (
    AnalyticsSummary,
    JobCountByStatus,
    JobCountByType,
    JobCreate,
    JobListItem,
    JobListResponse,
    JobQuestionCreate,
    JobQuestionResponse,
    JobQuestionUpdate,
    JobResponse,
    JobSkillCreate,
    JobSkillResponse,
    JobUpdate,
    PipelineStageCreate,
    PipelineStageResponse,
    PipelineStageReorderItem,
    PipelineStageUpdate,
    QuestionsReorderRequest,
)

# Roles that can manage jobs (everyone except candidates)
_HR_ROLES = {
    UserRole.HR, UserRole.HR_ADMIN, UserRole.HIRING_MANAGER,
    UserRole.RECRUITER, UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.ELITE_ADMIN,
}


class JobService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = JobRepository(db)

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _get_job_or_404(self, job_id: uuid.UUID) -> object:
        job = await self.repo.get_by_id(job_id)
        if job is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Job not found")
        return job

    def _assert_owner_or_admin(self, job: object, user_id: uuid.UUID, role: UserRole) -> None:
        posted_by = getattr(job, "posted_by", None)
        if role in {UserRole.ADMIN, UserRole.ELITE_ADMIN}:
            return
        if posted_by != user_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not the job owner")

    # ── Job CRUD ──────────────────────────────────────────────────────────────

    async def create_job(
        self, data: JobCreate, user_id: uuid.UUID
    ) -> JobResponse:
        job_data = data.model_dump(exclude_none=False)
        job = await self.repo.create(job_data, posted_by=user_id)
        return JobResponse.model_validate(job)

    async def list_jobs(
        self,
        *,
        user_id: uuid.UUID,
        role: UserRole,
        status: JobStatus | None = None,
        job_type: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> JobListResponse:
        # Admins see all; HR roles see only their own
        owner_filter: uuid.UUID | None = None
        if role not in {UserRole.ADMIN, UserRole.ELITE_ADMIN, UserRole.SUPERADMIN}:
            owner_filter = user_id

        skip = (page - 1) * page_size
        jobs, total = await self.repo.get_all(
            posted_by=owner_filter,
            status=status,
            job_type=job_type,
            search=search,
            skip=skip,
            limit=page_size,
        )
        items = [JobListItem.model_validate(j) for j in jobs]
        return JobListResponse(items=items, total=total, page=page, page_size=page_size)

    async def get_job(self, job_id: uuid.UUID) -> JobResponse:
        job = await self._get_job_or_404(job_id)
        return JobResponse.model_validate(job)

    async def update_job(
        self, job_id: uuid.UUID, data: JobUpdate, user_id: uuid.UUID, role: UserRole
    ) -> JobResponse:
        job = await self._get_job_or_404(job_id)
        self._assert_owner_or_admin(job, user_id, role)
        if job.status == JobStatus.CLOSED:  # type: ignore[union-attr]
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Cannot edit a closed job")
        update_data = data.model_dump(exclude_none=True)
        job = await self.repo.update(job, update_data)  # type: ignore[arg-type]
        return JobResponse.model_validate(job)

    async def delete_job(
        self, job_id: uuid.UUID, user_id: uuid.UUID, role: UserRole
    ) -> None:
        job = await self._get_job_or_404(job_id)
        self._assert_owner_or_admin(job, user_id, role)
        if job.status not in {JobStatus.DRAFT, JobStatus.CLOSED}:  # type: ignore[operator]
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Only draft or closed jobs can be deleted. Pause or close the job first.",
            )
        await self.repo.delete(job)  # type: ignore[arg-type]

    # ── Status transitions ────────────────────────────────────────────────────

    async def publish_job(
        self, job_id: uuid.UUID, user_id: uuid.UUID, role: UserRole
    ) -> JobResponse:
        job = await self._get_job_or_404(job_id)
        self._assert_owner_or_admin(job, user_id, role)
        if job.status != JobStatus.DRAFT and job.status != JobStatus.PAUSED:  # type: ignore[union-attr]
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail=f"Cannot publish a job with status '{job.status.value}'",  # type: ignore[union-attr]
            )
        job = await self.repo.update(job, {  # type: ignore[arg-type]
            "status": JobStatus.ACTIVE,
            "published_at": datetime.now(tz=timezone.utc),
        })

        # Real-time event: notify all users that a new job is live
        try:
            from app.core.event_emitter import emit_event
            await emit_event(
                "new_job_posted",
                {
                    "job_id": str(job_id),
                    "title": getattr(job, "title", ""),
                    "location": getattr(job, "location", ""),
                },
            )
        except Exception:
            pass

        return JobResponse.model_validate(job)

    async def pause_job(
        self, job_id: uuid.UUID, user_id: uuid.UUID, role: UserRole
    ) -> JobResponse:
        job = await self._get_job_or_404(job_id)
        self._assert_owner_or_admin(job, user_id, role)
        if job.status != JobStatus.ACTIVE:  # type: ignore[union-attr]
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail="Only active jobs can be paused"
            )
        job = await self.repo.update(job, {"status": JobStatus.PAUSED})  # type: ignore[arg-type]
        return JobResponse.model_validate(job)

    async def close_job(
        self, job_id: uuid.UUID, user_id: uuid.UUID, role: UserRole
    ) -> JobResponse:
        job = await self._get_job_or_404(job_id)
        self._assert_owner_or_admin(job, user_id, role)
        if job.status == JobStatus.CLOSED:  # type: ignore[union-attr]
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Job is already closed")
        job = await self.repo.update(job, {  # type: ignore[arg-type]
            "status": JobStatus.CLOSED,
            "closed_at": datetime.now(tz=timezone.utc),
        })
        return JobResponse.model_validate(job)

    async def clone_job(
        self, job_id: uuid.UUID, user_id: uuid.UUID
    ) -> JobResponse:
        source = await self._get_job_or_404(job_id)
        clone_data = {
            "title": f"Copy of {source.title}",  # type: ignore[union-attr]
            "description": source.description,  # type: ignore[union-attr]
            "requirements": source.requirements,  # type: ignore[union-attr]
            "location": source.location,  # type: ignore[union-attr]
            "job_type": source.job_type,  # type: ignore[union-attr]
            "department": source.department,  # type: ignore[union-attr]
            "salary_min": source.salary_min,  # type: ignore[union-attr]
            "salary_max": source.salary_max,  # type: ignore[union-attr]
            "currency": source.currency,  # type: ignore[union-attr]
            "experience_years_min": source.experience_years_min,  # type: ignore[union-attr]
            "experience_years_max": source.experience_years_max,  # type: ignore[union-attr]
            "status": JobStatus.DRAFT,
            "company_id": source.company_id,  # type: ignore[union-attr]
        }
        new_job = await self.repo.create(clone_data, posted_by=user_id)
        # Copy skills
        for skill in source.skills:  # type: ignore[union-attr]
            await self.repo.add_skill(new_job.id, skill.skill_name, skill.is_required)
        # Copy questions
        for q in source.questions:  # type: ignore[union-attr]
            await self.repo.add_question(new_job.id, {
                "question_text": q.question_text,
                "question_type": q.question_type,
                "options": q.options,
                "is_required": q.is_required,
                "display_order": q.display_order,
            })
        await self.repo.db.refresh(new_job)
        return JobResponse.model_validate(new_job)

    # ── Skills ────────────────────────────────────────────────────────────────

    async def add_skill(
        self, job_id: uuid.UUID, data: JobSkillCreate,
        user_id: uuid.UUID, role: UserRole,
    ) -> JobSkillResponse:
        job = await self._get_job_or_404(job_id)
        self._assert_owner_or_admin(job, user_id, role)
        skill = await self.repo.add_skill(job_id, data.skill_name, data.is_required)
        return JobSkillResponse.model_validate(skill)

    async def remove_skill(
        self, job_id: uuid.UUID, skill_id: uuid.UUID,
        user_id: uuid.UUID, role: UserRole,
    ) -> None:
        job = await self._get_job_or_404(job_id)
        self._assert_owner_or_admin(job, user_id, role)
        removed = await self.repo.remove_skill(job_id, skill_id)
        if not removed:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Skill not found")

    # ── Questions ─────────────────────────────────────────────────────────────

    async def create_question(
        self, job_id: uuid.UUID, data: JobQuestionCreate,
        user_id: uuid.UUID, role: UserRole,
    ) -> JobQuestionResponse:
        job = await self._get_job_or_404(job_id)
        self._assert_owner_or_admin(job, user_id, role)
        question = await self.repo.add_question(job_id, data.model_dump())
        return JobQuestionResponse.model_validate(question)

    async def update_question(
        self, job_id: uuid.UUID, question_id: uuid.UUID,
        data: JobQuestionUpdate, user_id: uuid.UUID, role: UserRole,
    ) -> JobQuestionResponse:
        job = await self._get_job_or_404(job_id)
        self._assert_owner_or_admin(job, user_id, role)
        question = await self.repo.get_question(job_id, question_id)
        if question is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Question not found")
        question = await self.repo.update_question(question, data.model_dump(exclude_none=True))
        return JobQuestionResponse.model_validate(question)

    async def delete_question(
        self, job_id: uuid.UUID, question_id: uuid.UUID,
        user_id: uuid.UUID, role: UserRole,
    ) -> None:
        job = await self._get_job_or_404(job_id)
        self._assert_owner_or_admin(job, user_id, role)
        question = await self.repo.get_question(job_id, question_id)
        if question is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Question not found")
        await self.repo.delete_question(question)

    async def reorder_questions(
        self, job_id: uuid.UUID, payload: QuestionsReorderRequest,
        user_id: uuid.UUID, role: UserRole,
    ) -> list[JobQuestionResponse]:
        job = await self._get_job_or_404(job_id)
        self._assert_owner_or_admin(job, user_id, role)
        await self.repo.reorder_questions(job_id, payload.question_ids)
        refreshed = await self.repo.get_by_id(job_id)
        return [JobQuestionResponse.model_validate(q) for q in refreshed.questions]  # type: ignore[union-attr]

    # ── Pipeline ──────────────────────────────────────────────────────────────

    async def add_pipeline_stage(
        self, job_id: uuid.UUID, data: PipelineStageCreate,
        user_id: uuid.UUID, role: UserRole,
    ) -> PipelineStageResponse:
        job = await self._get_job_or_404(job_id)
        self._assert_owner_or_admin(job, user_id, role)
        stage = await self.repo.add_pipeline_stage(job_id, data.stage_name, data.color)
        return PipelineStageResponse.model_validate(stage)

    async def update_pipeline_stage(
        self, job_id: uuid.UUID, stage_id: uuid.UUID,
        data: PipelineStageUpdate, user_id: uuid.UUID, role: UserRole,
    ) -> PipelineStageResponse:
        await self._get_job_or_404(job_id)
        stage = await self.repo.get_pipeline_stage(job_id, stage_id)
        if stage is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Stage not found")
        stage = await self.repo.update_pipeline_stage(stage, data.model_dump(exclude_none=True))
        return PipelineStageResponse.model_validate(stage)

    async def delete_pipeline_stage(
        self, job_id: uuid.UUID, stage_id: uuid.UUID,
        user_id: uuid.UUID, role: UserRole,
    ) -> None:
        job = await self._get_job_or_404(job_id)
        self._assert_owner_or_admin(job, user_id, role)
        stage = await self.repo.get_pipeline_stage(job_id, stage_id)
        if stage is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Stage not found")
        if stage.is_default:
            raise HTTPException(
                status.HTTP_409_CONFLICT, detail="Cannot delete a default pipeline stage"
            )
        await self.repo.delete_pipeline_stage(stage)

    async def reorder_pipeline(
        self, job_id: uuid.UUID, items: list[PipelineStageReorderItem],
        user_id: uuid.UUID, role: UserRole,
    ) -> list[PipelineStageResponse]:
        job = await self._get_job_or_404(job_id)
        self._assert_owner_or_admin(job, user_id, role)
        await self.repo.reorder_pipeline(
            job_id, [{"id": i.id, "stage_order": i.stage_order} for i in items]
        )
        refreshed = await self.repo.get_by_id(job_id)
        return [PipelineStageResponse.model_validate(s) for s in refreshed.pipeline_stages]  # type: ignore[union-attr]

    # ── Analytics ─────────────────────────────────────────────────────────────

    async def get_analytics_summary(
        self, user_id: uuid.UUID, role: UserRole
    ) -> AnalyticsSummary:
        owner_filter: uuid.UUID | None = None
        if role not in {UserRole.ADMIN, UserRole.ELITE_ADMIN, UserRole.SUPERADMIN}:
            owner_filter = user_id

        by_status = await self.repo.get_counts_by_status(owner_filter)
        by_type = await self.repo.get_counts_by_type(owner_filter)
        total_apps = await self.repo.get_total_applications(owner_filter)
        total_views = await self.repo.get_total_views(owner_filter)
        top_jobs = await self.repo.get_top_jobs(owner_filter)

        total = sum(by_status.values())
        active = by_status.get("active", 0)

        return AnalyticsSummary(
            total_jobs=total,
            active_jobs=active,
            total_applications=total_apps,
            total_views=total_views,
            by_status=JobCountByStatus(**{k: by_status.get(k, 0) for k in ["draft", "active", "paused", "closed"]}),
            by_type=JobCountByType(**{k: by_type.get(k, 0) for k in ["full_time", "part_time", "contract", "internship", "remote"]}),
            top_jobs=[JobListItem.model_validate(j) for j in top_jobs],
        )

    # ── Auto-archive (called from Celery) ─────────────────────────────────────

    async def auto_archive_old_jobs(self, older_than_days: int = 90) -> int:
        jobs = await self.repo.get_archivable_jobs(older_than_days)
        if not jobs:
            return 0
        job_ids = [j.id for j in jobs]
        return await self.repo.bulk_set_archived(job_ids)
