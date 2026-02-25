"""Job router — /jobs endpoints (no from __future__ import annotations)."""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_role
from app.models.job import JobStatus
from app.models.user import User, UserRole
from app.schemas.job import (
    AnalyticsSummary,
    JobCreate,
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
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])

_HR_ROLES = (
    UserRole.HR, UserRole.HR_ADMIN, UserRole.HIRING_MANAGER,
    UserRole.RECRUITER, UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.ELITE_ADMIN,
)


def _get_service(db: AsyncSession = Depends(get_db)) -> JobService:
    return JobService(db)


# ─── Job CRUD ─────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a draft job posting",
)
async def create_job(
    data: JobCreate,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> JobResponse:
    return await service.create_job(data, user_id=current_user.id)


@router.get(
    "",
    response_model=JobListResponse,
    summary="List job postings (paginated + filtered)",
)
async def list_jobs(
    status_filter: JobStatus | None = Query(None, alias="status"),
    job_type: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> JobListResponse:
    return await service.list_jobs(
        user_id=current_user.id,
        role=current_user.role,
        status=status_filter,
        job_type=job_type,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get a job posting by ID",
)
async def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> JobResponse:
    return await service.get_job(job_id)


@router.put(
    "/{job_id}",
    response_model=JobResponse,
    summary="Update a job posting",
)
async def update_job(
    job_id: uuid.UUID,
    data: JobUpdate,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> JobResponse:
    return await service.update_job(job_id, data, current_user.id, current_user.role)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a draft or closed job",
)
async def delete_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> None:
    await service.delete_job(job_id, current_user.id, current_user.role)


# ─── Status transitions ───────────────────────────────────────────────────────

@router.post(
    "/{job_id}/publish",
    response_model=JobResponse,
    summary="Publish a draft or paused job",
)
async def publish_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> JobResponse:
    return await service.publish_job(job_id, current_user.id, current_user.role)


@router.post(
    "/{job_id}/pause",
    response_model=JobResponse,
    summary="Pause an active job",
)
async def pause_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> JobResponse:
    return await service.pause_job(job_id, current_user.id, current_user.role)


@router.post(
    "/{job_id}/close",
    response_model=JobResponse,
    summary="Close a job posting",
)
async def close_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> JobResponse:
    return await service.close_job(job_id, current_user.id, current_user.role)


@router.post(
    "/{job_id}/clone",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone a job as a new draft",
)
async def clone_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> JobResponse:
    return await service.clone_job(job_id, current_user.id)


# ─── Skills ───────────────────────────────────────────────────────────────────

@router.post(
    "/{job_id}/skills",
    response_model=JobSkillResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a skill requirement to a job",
)
async def add_skill(
    job_id: uuid.UUID,
    data: JobSkillCreate,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> JobSkillResponse:
    return await service.add_skill(job_id, data, current_user.id, current_user.role)


@router.delete(
    "/{job_id}/skills/{skill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a skill from a job",
)
async def remove_skill(
    job_id: uuid.UUID,
    skill_id: uuid.UUID,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> None:
    await service.remove_skill(job_id, skill_id, current_user.id, current_user.role)


# ─── Screening questions ──────────────────────────────────────────────────────

@router.post(
    "/{job_id}/questions",
    response_model=JobQuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a screening question to a job",
)
async def add_question(
    job_id: uuid.UUID,
    data: JobQuestionCreate,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> JobQuestionResponse:
    return await service.create_question(job_id, data, current_user.id, current_user.role)


@router.put(
    "/{job_id}/questions/{question_id}",
    response_model=JobQuestionResponse,
    summary="Update a screening question",
)
async def update_question(
    job_id: uuid.UUID,
    question_id: uuid.UUID,
    data: JobQuestionUpdate,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> JobQuestionResponse:
    return await service.update_question(
        job_id, question_id, data, current_user.id, current_user.role
    )


@router.delete(
    "/{job_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a screening question",
)
async def delete_question(
    job_id: uuid.UUID,
    question_id: uuid.UUID,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> None:
    await service.delete_question(job_id, question_id, current_user.id, current_user.role)


@router.post(
    "/{job_id}/questions/reorder",
    response_model=list[JobQuestionResponse],
    summary="Reorder screening questions",
)
async def reorder_questions(
    job_id: uuid.UUID,
    payload: QuestionsReorderRequest,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> list[JobQuestionResponse]:
    return await service.reorder_questions(
        job_id, payload, current_user.id, current_user.role
    )


# ─── Pipeline stages ──────────────────────────────────────────────────────────

@router.get(
    "/{job_id}/pipeline",
    response_model=list[PipelineStageResponse],
    summary="Get Kanban pipeline stages for a job",
)
async def get_pipeline(
    job_id: uuid.UUID,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> list[PipelineStageResponse]:
    job = await service.get_job(job_id)
    return job.pipeline_stages


@router.post(
    "/{job_id}/pipeline",
    response_model=PipelineStageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a custom pipeline stage",
)
async def add_pipeline_stage(
    job_id: uuid.UUID,
    data: PipelineStageCreate,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> PipelineStageResponse:
    return await service.add_pipeline_stage(job_id, data, current_user.id, current_user.role)


@router.put(
    "/{job_id}/pipeline/{stage_id}",
    response_model=PipelineStageResponse,
    summary="Update a pipeline stage name/colour",
)
async def update_pipeline_stage(
    job_id: uuid.UUID,
    stage_id: uuid.UUID,
    data: PipelineStageUpdate,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> PipelineStageResponse:
    return await service.update_pipeline_stage(
        job_id, stage_id, data, current_user.id, current_user.role
    )


@router.delete(
    "/{job_id}/pipeline/{stage_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a custom pipeline stage",
)
async def delete_pipeline_stage(
    job_id: uuid.UUID,
    stage_id: uuid.UUID,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> None:
    await service.delete_pipeline_stage(job_id, stage_id, current_user.id, current_user.role)


@router.post(
    "/{job_id}/pipeline/reorder",
    response_model=list[PipelineStageResponse],
    summary="Reorder pipeline stages after drag-drop",
)
async def reorder_pipeline(
    job_id: uuid.UUID,
    items: list[PipelineStageReorderItem],
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> list[PipelineStageResponse]:
    return await service.reorder_pipeline(
        job_id, items, current_user.id, current_user.role
    )


# ─── Analytics (separate prefix /analytics) ──────────────────────────────────

analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])


@analytics_router.get(
    "/jobs/summary",
    response_model=AnalyticsSummary,
    summary="Recruiter analytics: job counts, top performing jobs",
)
async def jobs_analytics_summary(
    current_user: User = Depends(require_role(*_HR_ROLES)),
    service: JobService = Depends(_get_service),
) -> AnalyticsSummary:
    return await service.get_analytics_summary(current_user.id, current_user.role)
