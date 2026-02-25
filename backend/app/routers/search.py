"""Search endpoints — Module 6."""

import uuid

import structlog
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_role
from app.models.user import User, UserRole
from app.schemas.search import (
    BulkExportRequest,
    SavedSearchCreate,
    SavedSearchResponse,
    SearchCandidateRequest,
    SearchResult,
    TalentPoolAddCandidates,
    TalentPoolCreate,
    TalentPoolResponse,
)
from app.services import search_service

log = structlog.get_logger("donehr.search_router")

# HR roles that may search candidates
_HR_ROLES = [
    UserRole.HR,
    UserRole.HR_ADMIN,
    UserRole.HIRING_MANAGER,
    UserRole.RECRUITER,
    UserRole.SUPERADMIN,
    UserRole.ADMIN,
    UserRole.ELITE_ADMIN,
]

router = APIRouter(prefix="/api/v1/search", tags=["search"])


# ── Candidate search ──────────────────────────────────────────────────────────

@router.post(
    "/candidates",
    response_model=SearchResult,
    summary="Search candidates with advanced filters",
)
async def search_candidates(
    filters: SearchCandidateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*_HR_ROLES)),
) -> SearchResult:
    return await search_service.search_candidates(db, filters, current_user.id)


# ── Saved searches ────────────────────────────────────────────────────────────

@router.post(
    "/saved",
    response_model=SavedSearchResponse,
    status_code=201,
    summary="Save a named search filter",
)
async def create_saved_search(
    data: SavedSearchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*_HR_ROLES)),
) -> SavedSearchResponse:
    return await search_service.create_saved_search(db, current_user.id, data)


@router.get(
    "/saved",
    response_model=list[SavedSearchResponse],
    summary="List saved searches",
)
async def list_saved_searches(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*_HR_ROLES)),
) -> list[SavedSearchResponse]:
    return await search_service.list_saved_searches(db, current_user.id)


@router.delete(
    "/saved/{search_id}",
    status_code=204,
    summary="Delete a saved search",
)
async def delete_saved_search(
    search_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*_HR_ROLES)),
) -> None:
    await search_service.delete_saved_search(db, current_user.id, search_id)


# ── Talent pools ──────────────────────────────────────────────────────────────

@router.post(
    "/pools",
    response_model=TalentPoolResponse,
    status_code=201,
    summary="Create a talent pool",
)
async def create_talent_pool(
    data: TalentPoolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*_HR_ROLES)),
) -> TalentPoolResponse:
    return await search_service.create_talent_pool(db, current_user.id, data)


@router.get(
    "/pools",
    response_model=list[TalentPoolResponse],
    summary="List talent pools",
)
async def list_talent_pools(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*_HR_ROLES)),
) -> list[TalentPoolResponse]:
    return await search_service.list_talent_pools(db, current_user.id)


@router.post(
    "/pools/{pool_id}/candidates",
    summary="Add candidates to talent pool",
)
async def add_to_pool(
    pool_id: uuid.UUID,
    data: TalentPoolAddCandidates,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*_HR_ROLES)),
) -> dict:
    return await search_service.add_to_talent_pool(
        db, current_user.id, pool_id, data
    )


# ── Bulk CSV export ───────────────────────────────────────────────────────────

@router.post(
    "/export/csv",
    summary="Export selected candidates as CSV",
)
async def export_csv(
    data: BulkExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*_HR_ROLES)),
) -> Response:
    csv_content = await search_service.export_candidates_csv(db, data)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=candidates.csv"
        },
    )
