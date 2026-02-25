"""Application endpoints — job search, apply, track, alerts."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_role
from app.models.user import User, UserRole
from app.schemas.application import (
    ApplicationListItem,
    ApplicationResponse,
    ApplyRequest,
    JobAlertCreate,
    JobAlertResponse,
    SalaryBenchmark,
)
from app.services.application_service import ApplicationService
from app.schemas.job import JobResponse

router = APIRouter(tags=["Applications"])

_CANDIDATE_ROLES = [UserRole.CANDIDATE]


def _svc(db: AsyncSession = Depends(get_db)) -> ApplicationService:
    return ApplicationService(db)


# ── Public job search ─────────────────────────────────────────────────────────

@router.get(
    "/jobs/search",
    summary="Search active jobs (public)",
)
async def search_jobs(
    q: Optional[str] = Query(None, description="Search keyword"),
    location: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    salary_min: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    svc: ApplicationService = Depends(_svc),
):
    return await svc.search_jobs(q=q, location=location, job_type=job_type, salary_min=salary_min, page=page, limit=limit)


@router.get(
    "/jobs/{job_id}/detail",
    summary="Get active job detail",
)
async def get_job_detail(
    job_id: uuid.UUID,
    svc: ApplicationService = Depends(_svc),
):
    return await svc.get_job_detail(job_id)


# ── Apply ─────────────────────────────────────────────────────────────────────

@router.post(
    "/jobs/{job_id}/apply",
    response_model=ApplicationResponse,
    status_code=201,
    summary="Apply to a job",
)
async def apply_to_job(
    job_id: uuid.UUID,
    data: ApplyRequest,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: ApplicationService = Depends(_svc),
):
    return await svc.apply(current_user.id, job_id, data)


# ── My applications ───────────────────────────────────────────────────────────

@router.get(
    "/candidates/applications",
    response_model=list[ApplicationListItem],
    summary="List my applications",
)
async def get_my_applications(
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: ApplicationService = Depends(_svc),
):
    return await svc.get_my_applications(current_user.id)


@router.get(
    "/candidates/applications/{app_id}",
    response_model=ApplicationResponse,
    summary="Get application detail with timeline",
)
async def get_application_detail(
    app_id: uuid.UUID,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: ApplicationService = Depends(_svc),
):
    return await svc.get_application_detail(current_user.id, app_id)


@router.delete(
    "/candidates/applications/{app_id}",
    status_code=204,
    summary="Withdraw application",
)
async def withdraw_application(
    app_id: uuid.UUID,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: ApplicationService = Depends(_svc),
):
    await svc.withdraw(current_user.id, app_id)


# ── Recommendations ───────────────────────────────────────────────────────────

@router.get(
    "/candidates/recommendations",
    summary="Get personalized job recommendations",
)
async def get_recommendations(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: ApplicationService = Depends(_svc),
):
    return await svc.get_recommendations(current_user.id, limit=limit)


# ── Salary benchmark ──────────────────────────────────────────────────────────

@router.get(
    "/candidates/salary-benchmark",
    response_model=list[SalaryBenchmark],
    summary="Get salary benchmark data",
)
async def get_salary_benchmark(
    role: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    svc: ApplicationService = Depends(_svc),
):
    return svc.get_salary_benchmark(role=role, location=location)


# ── Job alerts ────────────────────────────────────────────────────────────────

@router.post(
    "/candidates/alerts",
    response_model=JobAlertResponse,
    status_code=201,
    summary="Create job alert",
)
async def create_alert(
    data: JobAlertCreate,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: ApplicationService = Depends(_svc),
):
    return await svc.create_alert(current_user.id, data)


@router.get(
    "/candidates/alerts",
    response_model=list[JobAlertResponse],
    summary="List my job alerts",
)
async def get_alerts(
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: ApplicationService = Depends(_svc),
):
    return await svc.get_alerts(current_user.id)


@router.delete(
    "/candidates/alerts/{alert_id}",
    status_code=204,
    summary="Delete job alert",
)
async def delete_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: ApplicationService = Depends(_svc),
):
    await svc.delete_alert(current_user.id, alert_id)
