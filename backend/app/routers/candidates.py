"""Candidate profile endpoints."""
import uuid

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_role
from app.models.user import User, UserRole
from app.schemas.candidate import (
    CandidateProfileResponse,
    CandidateProfileUpdate,
    CandidateSkillCreate,
    CandidateSkillResponse,
    CertificationCreate,
    CertificationResponse,
    EducationCreate,
    EducationResponse,
    ProfileStrengthResponse,
    ProjectCreate,
    ProjectResponse,
    WorkExperienceCreate,
    WorkExperienceResponse,
)
from app.services.candidate_service import CandidateService

router = APIRouter(prefix="/candidates", tags=["Candidates"])

_CANDIDATE_ROLES = [UserRole.CANDIDATE]


def _svc(db: AsyncSession = Depends(get_db)) -> CandidateService:
    return CandidateService(db)


# ── Profile ───────────────────────────────────────────────────────────────────

@router.get(
    "/profile",
    response_model=CandidateProfileResponse,
    summary="Get my candidate profile",
)
async def get_profile(
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: CandidateService = Depends(_svc),
):
    return await svc.get_or_create_profile(current_user.id)


@router.patch(
    "/profile",
    response_model=CandidateProfileResponse,
    summary="Update my candidate profile",
)
async def update_profile(
    data: CandidateProfileUpdate,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: CandidateService = Depends(_svc),
):
    return await svc.update_profile(current_user.id, data)


@router.post(
    "/profile/resume",
    response_model=CandidateProfileResponse,
    summary="Upload resume (PDF, max 5 MB)",
)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: CandidateService = Depends(_svc),
):
    return await svc.upload_resume(current_user.id, file)


@router.get(
    "/profile/strength",
    response_model=ProfileStrengthResponse,
    summary="Get profile strength score",
)
async def get_profile_strength(
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: CandidateService = Depends(_svc),
):
    return await svc.get_profile_strength(current_user.id)


# ── Work Experience ───────────────────────────────────────────────────────────

@router.post(
    "/profile/work-experiences",
    response_model=WorkExperienceResponse,
    status_code=201,
    summary="Add work experience",
)
async def add_work_experience(
    data: WorkExperienceCreate,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: CandidateService = Depends(_svc),
):
    return await svc.add_work_experience(current_user.id, data)


@router.delete(
    "/profile/work-experiences/{exp_id}",
    status_code=204,
    summary="Delete work experience",
)
async def delete_work_experience(
    exp_id: uuid.UUID,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: CandidateService = Depends(_svc),
):
    await svc.delete_work_experience(current_user.id, exp_id)


# ── Education ─────────────────────────────────────────────────────────────────

@router.post(
    "/profile/educations",
    response_model=EducationResponse,
    status_code=201,
    summary="Add education",
)
async def add_education(
    data: EducationCreate,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: CandidateService = Depends(_svc),
):
    return await svc.add_education(current_user.id, data)


@router.delete(
    "/profile/educations/{edu_id}",
    status_code=204,
    summary="Delete education",
)
async def delete_education(
    edu_id: uuid.UUID,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: CandidateService = Depends(_svc),
):
    await svc.delete_education(current_user.id, edu_id)


# ── Certifications ────────────────────────────────────────────────────────────

@router.post(
    "/profile/certifications",
    response_model=CertificationResponse,
    status_code=201,
    summary="Add certification",
)
async def add_certification(
    data: CertificationCreate,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: CandidateService = Depends(_svc),
):
    return await svc.add_certification(current_user.id, data)


@router.delete(
    "/profile/certifications/{cert_id}",
    status_code=204,
    summary="Delete certification",
)
async def delete_certification(
    cert_id: uuid.UUID,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: CandidateService = Depends(_svc),
):
    await svc.delete_certification(current_user.id, cert_id)


# ── Projects ──────────────────────────────────────────────────────────────────

@router.post(
    "/profile/projects",
    response_model=ProjectResponse,
    status_code=201,
    summary="Add project",
)
async def add_project(
    data: ProjectCreate,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: CandidateService = Depends(_svc),
):
    return await svc.add_project(current_user.id, data)


@router.delete(
    "/profile/projects/{proj_id}",
    status_code=204,
    summary="Delete project",
)
async def delete_project(
    proj_id: uuid.UUID,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: CandidateService = Depends(_svc),
):
    await svc.delete_project(current_user.id, proj_id)


# ── Skills ────────────────────────────────────────────────────────────────────

@router.post(
    "/profile/skills",
    response_model=CandidateSkillResponse,
    status_code=201,
    summary="Add skill",
)
async def add_skill(
    data: CandidateSkillCreate,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: CandidateService = Depends(_svc),
):
    return await svc.add_skill(current_user.id, data)


@router.delete(
    "/profile/skills/{skill_id}",
    status_code=204,
    summary="Delete skill",
)
async def delete_skill(
    skill_id: uuid.UUID,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    svc: CandidateService = Depends(_svc),
):
    await svc.delete_skill(current_user.id, skill_id)
