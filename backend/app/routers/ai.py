"""AI endpoints — resume parsing, summaries, match scores, chatbot."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_role
from app.models.user import User, UserRole
from app.schemas.ai import (
    AISummaryResponse,
    CandidateComparisonResponse,
    ChatRequest,
    ChatResponse,
    CompareRequest,
    GenerateJDRequest,
    GenerateJDResponse,
    MatchScoreResponse,
    ParsedResumeFields,
    RankingResponse,
    RejectionEmailRequest,
    RejectionEmailResponse,
    ResumeSummaryResponse,
    ResumeOptimizerResponse,
)
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["AI"])

_HR_ROLES = [
    UserRole.HR, UserRole.HR_ADMIN, UserRole.HIRING_MANAGER,
    UserRole.RECRUITER, UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.ELITE_ADMIN,
]
_CANDIDATE_ROLES = [UserRole.CANDIDATE]


def _db(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db


# ── Resume Parser (candidate) ─────────────────────────────────────────────────

@router.post(
    "/parse-resume",
    response_model=ParsedResumeFields,
    summary="Parse resume PDF → extract structured profile fields",
)
async def parse_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    db: AsyncSession = Depends(_db),
):
    pdf_bytes = await file.read()
    return await ai_service.parse_resume_pdf(db, current_user.id, pdf_bytes)


# ── Resume Summary (HR) ───────────────────────────────────────────────────────

@router.get(
    "/resume-summary/{candidate_id}",
    response_model=ResumeSummaryResponse,
    summary="Get AI summary of a candidate (HR only)",
)
async def get_resume_summary(
    candidate_id: uuid.UUID,
    refresh: bool = Query(False, description="Force regenerate (bypass cache)"),
    current_user: User = Depends(require_role(*_HR_ROLES)),
    db: AsyncSession = Depends(_db),
):
    return await ai_service.get_resume_summary(db, candidate_id, force_refresh=refresh)


# ── Match Score (HR) ──────────────────────────────────────────────────────────

@router.get(
    "/match-score/{application_id}",
    response_model=MatchScoreResponse,
    summary="Get AI match score for an application (HR only)",
)
async def get_match_score(
    application_id: uuid.UUID,
    refresh: bool = Query(False),
    current_user: User = Depends(require_role(*_HR_ROLES)),
    db: AsyncSession = Depends(_db),
):
    return await ai_service.get_match_score(db, application_id, force_refresh=refresh)


@router.post(
    "/match-score/{application_id}/enqueue",
    status_code=202,
    summary="Queue background match score computation",
)
async def enqueue_match_score(
    application_id: uuid.UUID,
    current_user: User = Depends(require_role(*_HR_ROLES)),
):
    from app.tasks.ai_tasks import compute_match_score
    compute_match_score.delay(str(application_id))
    return {"status": "queued", "application_id": str(application_id)}


# ── Candidate Comparison (HR) ─────────────────────────────────────────────────

@router.post(
    "/compare-candidates",
    response_model=CandidateComparisonResponse,
    summary="Compare 2-3 candidates side-by-side (HR only)",
)
async def compare_candidates(
    req: CompareRequest,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    db: AsyncSession = Depends(_db),
):
    return await ai_service.compare_candidates(db, req.application_ids)


# ── Auto Ranking (HR) ─────────────────────────────────────────────────────────

@router.post(
    "/rank-applicants/{job_id}",
    status_code=202,
    summary="Queue AI ranking of all applicants for a job",
)
async def rank_applicants_queue(
    job_id: uuid.UUID,
    current_user: User = Depends(require_role(*_HR_ROLES)),
):
    from app.tasks.ai_tasks import rank_applicants_task
    rank_applicants_task.delay(str(job_id))
    return {"status": "queued", "job_id": str(job_id)}


@router.get(
    "/rank-applicants/{job_id}",
    response_model=RankingResponse,
    summary="Get cached ranking for a job (HR only)",
)
async def get_ranking(
    job_id: uuid.UUID,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    db: AsyncSession = Depends(_db),
):
    return await ai_service.rank_applicants(db, job_id)


# ── JD Generator (HR) ────────────────────────────────────────────────────────

@router.post(
    "/generate-jd",
    response_model=GenerateJDResponse,
    summary="Generate a job description from role + keywords (HR only)",
)
async def generate_jd(
    req: GenerateJDRequest,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    db: AsyncSession = Depends(_db),
):
    return await ai_service.generate_job_description(db, req)


# ── Rejection Email Drafter (HR) ──────────────────────────────────────────────

@router.post(
    "/rejection-email",
    response_model=RejectionEmailResponse,
    summary="Draft a rejection email for an applicant (HR only)",
)
async def draft_rejection_email(
    req: RejectionEmailRequest,
    current_user: User = Depends(require_role(*_HR_ROLES)),
    db: AsyncSession = Depends(_db),
):
    return await ai_service.draft_rejection_email(db, req)


# ── Resume Optimizer (candidate) ──────────────────────────────────────────────

@router.get(
    "/optimize-resume",
    response_model=ResumeOptimizerResponse,
    summary="Get AI resume optimization tips (candidate only)",
)
async def optimize_resume(
    refresh: bool = Query(False),
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    db: AsyncSession = Depends(_db),
):
    return await ai_service.optimize_resume(db, current_user.id, force_refresh=refresh)


# ── Career Chatbot (candidate) ────────────────────────────────────────────────

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="AI career coaching chatbot (candidate only)",
)
async def chat(
    req: ChatRequest,
    current_user: User = Depends(require_role(*_CANDIDATE_ROLES)),
    db: AsyncSession = Depends(_db),
):
    return await ai_service.chat(db, current_user.id, req)
