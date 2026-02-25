"""Search service: orchestrates repository, Redis caching, analytics."""
from __future__ import annotations

import hashlib
import json
import uuid

import structlog
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import get_redis
from app.models.saved_search import SavedSearch, SearchAnalytic, TalentPool, TalentPoolCandidate
from app.models.candidate import CandidateProfile
from app.repositories.search_repository import CandidateSearchRepository
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

log = structlog.get_logger("donehr.search_service")
_repo = CandidateSearchRepository()

CACHE_TTL = 600  # 10 minutes


# ── Cache helpers ──────────────────────────────────────────────────────────────

def _cache_key(filters: SearchCandidateRequest) -> str:
    """Build a deterministic Redis key from the filter object (excluding cursor/page_size)."""
    d = filters.model_dump(exclude={"cursor", "page_size"}, mode="json")
    raw = json.dumps(d, sort_keys=True, default=str)
    digest = hashlib.md5(raw.encode()).hexdigest()
    return f"search:candidates:{digest}"


async def _get_cached(key: str) -> SearchResult | None:
    try:
        redis = get_redis()
        val = await redis.get(key)
        if val:
            return SearchResult.model_validate_json(val)
    except Exception:
        pass
    return None


async def _set_cached(key: str, result: SearchResult) -> None:
    try:
        redis = get_redis()
        await redis.set(key, result.model_dump_json(), ex=CACHE_TTL)
    except Exception:
        pass


# ── Main search ────────────────────────────────────────────────────────────────

async def search_candidates(
    db: AsyncSession,
    filters: SearchCandidateRequest,
    user_id: uuid.UUID,
) -> SearchResult:
    cache_key = _cache_key(filters)

    # Try cache first (only for first page — cursored pages not cached)
    if not filters.cursor:
        cached = await _get_cached(cache_key)
        if cached:
            cached.cached = True
            return cached

    result = await _repo.search(db, filters)

    # Cache first page result
    if not filters.cursor:
        await _set_cached(cache_key, result)

    # Log analytics (fire-and-forget style — don't block on failures)
    try:
        analytic = SearchAnalytic(
            user_id=user_id,
            filters=filters.model_dump(mode="json", exclude={"cursor"}, exclude_none=True),
            result_count=result.total,
        )
        db.add(analytic)
        await db.commit()
    except Exception as exc:
        log.warning("search_analytics_failed", error=str(exc))

    return result


# ── Saved searches ─────────────────────────────────────────────────────────────

async def create_saved_search(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: SavedSearchCreate,
) -> SavedSearchResponse:
    ss = SavedSearch(user_id=user_id, name=data.name, filters=data.filters)
    db.add(ss)
    await db.commit()
    await db.refresh(ss)
    return SavedSearchResponse(
        id=str(ss.id),
        name=ss.name,
        filters=ss.filters,
        created_at=ss.created_at.isoformat(),
    )


async def list_saved_searches(
    db: AsyncSession, user_id: uuid.UUID
) -> list[SavedSearchResponse]:
    rows = await db.scalars(
        select(SavedSearch)
        .where(SavedSearch.user_id == user_id)
        .order_by(SavedSearch.created_at.desc())
    )
    return [
        SavedSearchResponse(
            id=str(r.id),
            name=r.name,
            filters=r.filters,
            created_at=r.created_at.isoformat(),
        )
        for r in rows.all()
    ]


async def delete_saved_search(
    db: AsyncSession, user_id: uuid.UUID, search_id: uuid.UUID
) -> None:
    row = await db.scalar(
        select(SavedSearch).where(
            SavedSearch.id == search_id,
            SavedSearch.user_id == user_id,
        )
    )
    if not row:
        raise HTTPException(status_code=404, detail="Saved search not found")
    await db.delete(row)
    await db.commit()


# ── Talent pool ────────────────────────────────────────────────────────────────

async def create_talent_pool(
    db: AsyncSession, user_id: uuid.UUID, data: TalentPoolCreate
) -> TalentPoolResponse:
    pool = TalentPool(user_id=user_id, name=data.name)
    db.add(pool)
    await db.commit()
    await db.refresh(pool)
    return TalentPoolResponse(
        id=str(pool.id),
        name=pool.name,
        candidate_count=0,
        created_at=pool.created_at.isoformat(),
    )


async def list_talent_pools(
    db: AsyncSession, user_id: uuid.UUID
) -> list[TalentPoolResponse]:
    rows = await db.scalars(
        select(TalentPool)
        .where(TalentPool.user_id == user_id)
        .order_by(TalentPool.created_at.desc())
    )
    return [
        TalentPoolResponse(
            id=str(p.id),
            name=p.name,
            candidate_count=len(p.candidates),
            created_at=p.created_at.isoformat(),
        )
        for p in rows.all()
    ]


async def add_to_talent_pool(
    db: AsyncSession,
    user_id: uuid.UUID,
    pool_id: uuid.UUID,
    data: TalentPoolAddCandidates,
) -> dict:
    pool = await db.scalar(
        select(TalentPool).where(
            TalentPool.id == pool_id, TalentPool.user_id == user_id
        )
    )
    if not pool:
        raise HTTPException(status_code=404, detail="Talent pool not found")

    added = 0
    for cid_str in data.candidate_ids:
        try:
            cid = uuid.UUID(cid_str)
        except ValueError:
            continue
        # Skip if already in pool
        existing = await db.scalar(
            select(TalentPoolCandidate).where(
                TalentPoolCandidate.pool_id == pool_id,
                TalentPoolCandidate.candidate_id == cid,
            )
        )
        if not existing:
            db.add(
                TalentPoolCandidate(
                    pool_id=pool_id,
                    candidate_id=cid,
                    notes=data.notes,
                )
            )
            added += 1

    await db.commit()
    return {"added": added, "pool_id": str(pool_id)}


# ── CSV export ─────────────────────────────────────────────────────────────────

async def export_candidates_csv(
    db: AsyncSession, data: BulkExportRequest
) -> str:
    """Return a CSV string for the requested candidate IDs."""
    ids = []
    for cid_str in data.candidate_ids:
        try:
            ids.append(uuid.UUID(cid_str))
        except ValueError:
            pass

    if not ids:
        raise HTTPException(status_code=422, detail="No valid candidate IDs provided")

    rows = await db.scalars(
        select(CandidateProfile).where(CandidateProfile.id.in_(ids))
    )
    profiles = list(rows.all())

    lines = [
        "Name,Headline,Location,Experience (yrs),Skills,Notice Period (days),"
        "Min CTC (INR),Max CTC (INR),Profile Strength,Resume"
    ]
    for p in profiles:
        skill_str = "|".join(s.skill_name for s in p.skills)
        lines.append(
            ",".join(
                [
                    _csv_esc(p.full_name),
                    _csv_esc(p.headline),
                    _csv_esc(p.location),
                    str(p.years_of_experience or ""),
                    _csv_esc(skill_str),
                    str(p.notice_period_days or ""),
                    str(p.desired_salary_min or ""),
                    str(p.desired_salary_max or ""),
                    str(p.profile_strength),
                    _csv_esc(p.resume_filename),
                ]
            )
        )
    return "\n".join(lines)


def _csv_esc(val: str | None) -> str:
    if val is None:
        return ""
    escaped = val.replace('"', '""')
    if "," in escaped or '"' in escaped or "\n" in escaped:
        return f'"{escaped}"'
    return escaped
