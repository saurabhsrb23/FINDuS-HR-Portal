"""Dynamic candidate search query builder for Module 6."""
from __future__ import annotations

import base64
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from sqlalchemy import Select, and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.ai_summary import AISummary, SummaryType
from app.models.candidate import CandidateProfile, CandidateSkill, Education
from app.models.user import User
from app.schemas.search import (
    CandidateSearchItem,
    EducationTier,
    SearchCandidateRequest,
    SearchResult,
    SkillResult,
    SortBy,
    WorkPreference,
)
from app.utils.boolean_search_parser import parse_boolean_search

log = structlog.get_logger("donehr.search_repo")

# ── Cursor encoding ────────────────────────────────────────────────────────────

def _encode_cursor(updated_at: datetime, row_id: uuid.UUID) -> str:
    raw = f"{updated_at.isoformat()}|{row_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    ts_str, id_str = raw.split("|", 1)
    return datetime.fromisoformat(ts_str), uuid.UUID(id_str)


# ── Education tier detection ───────────────────────────────────────────────────

_UG_KEYWORDS = ("b.tech", "b.e.", "be ", "b.sc", "bsc", "b.ca", "bca", "bachelor")
_PG_KEYWORDS = ("m.tech", "m.e.", "me ", "mba", "m.sc", "msc", "master", "mca", "m.ca")
_PHD_KEYWORDS = ("ph.d", "phd", "doctor", "d.phil")


def _matches_education_tier(degree: str | None, tier: EducationTier) -> bool:
    if tier == EducationTier.ANY or not degree:
        return True
    low = degree.lower()
    if tier == EducationTier.UNDERGRADUATE:
        return any(k in low for k in _UG_KEYWORDS)
    if tier == EducationTier.POSTGRADUATE:
        return any(k in low for k in _PG_KEYWORDS)
    if tier == EducationTier.PHD:
        return any(k in low for k in _PHD_KEYWORDS)
    return True


# ── Main repository ───────────────────────────────────────────────────────────

class CandidateSearchRepository:
    async def search(
        self,
        db: AsyncSession,
        filters: SearchCandidateRequest,
    ) -> SearchResult:
        q = self._build_base_query(filters)
        total = await self._count(db, filters)
        profiles = await self._fetch_page(db, q, filters)

        candidates = [
            await self._to_item(db, p, filters)
            for p in profiles
        ]

        next_cursor: str | None = None
        if len(profiles) == filters.page_size and profiles:
            last = profiles[-1]
            next_cursor = _encode_cursor(last.updated_at, last.id)

        return SearchResult(
            total=total,
            candidates=candidates,
            next_cursor=next_cursor,
            page_size=filters.page_size,
        )

    # ── Query construction ─────────────────────────────────────────────────────

    def _build_base_query(self, filters: SearchCandidateRequest) -> Select:
        q: Select = (
            select(CandidateProfile)
            .join(User, CandidateProfile.user_id == User.id)
            .where(User.is_active.is_(True))
            .where(User.deleted_at.is_(None))
        )

        # ── Full-text boolean query ─────────────────────────────────────────
        if filters.query:
            tsq = parse_boolean_search(filters.query)
            if tsq:
                # Extract individual terms (strip tsquery operators) for skill matching
                terms = [
                    w.strip()
                    for w in re.split(r"[&|!()\s<>\*:]+", tsq)
                    if w.strip() and len(w.strip()) >= 2
                ]

                conditions: list[Any] = []

                # Condition 1: full-text search on headline/summary/role/location/name
                conditions.append(
                    CandidateProfile.search_vector.op("@@")(
                        func.to_tsquery("english", tsq)
                    )
                )

                # Condition 2: skill name match — catches candidates whose skills
                # contain the query terms even if not in their text fields
                if terms:
                    conditions.append(
                        CandidateProfile.id.in_(
                            select(CandidateSkill.candidate_id).where(
                                or_(
                                    *[
                                        CandidateSkill.skill_name.ilike(f"%{term}%")
                                        for term in terms
                                    ]
                                )
                            ).scalar_subquery()
                        )
                    )

                try:
                    q = q.where(or_(*conditions))
                except Exception:
                    pass  # malformed tsquery → skip filter

        # ── Skills filter ──────────────────────────────────────────────────
        if filters.skills:
            skill_clauses = []
            for sf in filters.skills:
                conds = [
                    CandidateSkill.skill_name.ilike(f"%{sf.skill}%")
                ]
                if sf.min_years is not None:
                    conds.append(CandidateSkill.years_exp >= sf.min_years)
                skill_clauses.append(
                    select(CandidateSkill.candidate_id)
                    .where(and_(*conds))
                    .scalar_subquery()
                )

            if filters.skill_match.value == "AND":
                for subq in skill_clauses:
                    q = q.where(CandidateProfile.id.in_(subq))
            else:  # OR
                combined = select(CandidateSkill.candidate_id).where(
                    or_(
                        *[
                            CandidateSkill.skill_name.ilike(f"%{sf.skill}%")
                            for sf in filters.skills
                        ]
                    )
                ).scalar_subquery()
                q = q.where(CandidateProfile.id.in_(combined))

        # ── Experience range ────────────────────────────────────────────────
        if filters.experience_min is not None:
            q = q.where(CandidateProfile.years_of_experience >= filters.experience_min)
        if filters.experience_max is not None:
            q = q.where(CandidateProfile.years_of_experience <= filters.experience_max)

        # ── Location (partial match) ────────────────────────────────────────
        if filters.location:
            q = q.where(
                CandidateProfile.location.ilike(f"%{filters.location}%")
            )

        # ── Notice period ───────────────────────────────────────────────────
        if filters.notice_period_max_days is not None:
            q = q.where(
                CandidateProfile.notice_period_days <= filters.notice_period_max_days
            )

        # ── CTC (stored in absolute INR; filters in lakhs) ──────────────────
        if filters.ctc_min is not None:
            q = q.where(
                CandidateProfile.desired_salary_min >= filters.ctc_min * 100_000
            )
        if filters.ctc_max is not None:
            q = q.where(
                CandidateProfile.desired_salary_max <= filters.ctc_max * 100_000
            )

        # ── Profile strength ────────────────────────────────────────────────
        if filters.profile_strength_min is not None:
            q = q.where(
                CandidateProfile.profile_strength >= filters.profile_strength_min
            )

        # ── Work preference ─────────────────────────────────────────────────
        if filters.work_preference == WorkPreference.REMOTE:
            q = q.where(CandidateProfile.open_to_remote.is_(True))
        elif filters.work_preference == WorkPreference.ONSITE:
            q = q.where(CandidateProfile.open_to_remote.is_(False))

        # ── Last active ─────────────────────────────────────────────────────
        if filters.last_active_days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(
                days=filters.last_active_days
            )
            q = q.where(CandidateProfile.updated_at >= cutoff)

        # ── Education tier ──────────────────────────────────────────────────
        if filters.education_tier != EducationTier.ANY:
            kw_map = {
                EducationTier.UNDERGRADUATE: _UG_KEYWORDS,
                EducationTier.POSTGRADUATE: _PG_KEYWORDS,
                EducationTier.PHD: _PHD_KEYWORDS,
            }
            keywords = kw_map[filters.education_tier]
            edu_clauses = [
                Education.degree.ilike(f"%{k}%") for k in keywords
            ]
            edu_subq = (
                select(Education.candidate_id)
                .where(or_(*edu_clauses))
                .scalar_subquery()
            )
            q = q.where(CandidateProfile.id.in_(edu_subq))

        return q

    async def _count(self, db: AsyncSession, filters: SearchCandidateRequest) -> int:
        base = self._build_base_query(filters)
        count_q = select(func.count()).select_from(base.subquery())
        result = await db.scalar(count_q)
        return int(result or 0)

    async def _fetch_page(
        self,
        db: AsyncSession,
        q: Select,
        filters: SearchCandidateRequest,
    ) -> list[CandidateProfile]:
        # ── Cursor ─────────────────────────────────────────────────────────
        if filters.cursor:
            try:
                cur_ts, cur_id = _decode_cursor(filters.cursor)
                q = q.where(
                    or_(
                        CandidateProfile.updated_at < cur_ts,
                        and_(
                            CandidateProfile.updated_at == cur_ts,
                            CandidateProfile.id < cur_id,
                        ),
                    )
                )
            except Exception:
                pass  # bad cursor → ignore and start from beginning

        # ── Sort ────────────────────────────────────────────────────────────
        if filters.sort_by == SortBy.EXPERIENCE:
            q = q.order_by(
                CandidateProfile.years_of_experience.desc().nulls_last(),
                CandidateProfile.updated_at.desc(),
            )
        elif filters.sort_by == SortBy.RECENTLY_ACTIVE:
            q = q.order_by(CandidateProfile.updated_at.desc())
        elif filters.sort_by == SortBy.PROFILE_STRENGTH:
            q = q.order_by(
                CandidateProfile.profile_strength.desc(),
                CandidateProfile.updated_at.desc(),
            )
        else:  # RELEVANCE (default): blend profile_strength + recency
            q = q.order_by(
                CandidateProfile.profile_strength.desc(),
                CandidateProfile.updated_at.desc(),
            )

        q = q.limit(filters.page_size)
        result = await db.execute(q)
        return list(result.scalars().all())

    # ── Row → response ─────────────────────────────────────────────────────────

    async def _to_item(
        self,
        db: AsyncSession,
        profile: CandidateProfile,
        filters: SearchCandidateRequest,
    ) -> CandidateSearchItem:
        # Skills with match highlighting — includes both skills filter AND boolean query terms
        filter_skills_lower: set[str] = {sf.skill.lower() for sf in filters.skills}
        if filters.query:
            tsq = parse_boolean_search(filters.query)
            if tsq:
                query_terms = {
                    w.strip().lower()
                    for w in re.split(r"[&|!()\s<>\*:]+", tsq)
                    if w.strip() and len(w.strip()) >= 2
                }
                filter_skills_lower |= query_terms

        skill_results = [
            SkillResult(
                skill_name=s.skill_name,
                proficiency=s.proficiency,
                years_exp=s.years_exp,
                matched=s.skill_name.lower() in filter_skills_lower
                or any(
                    fs in s.skill_name.lower() for fs in filter_skills_lower
                ),
            )
            for s in profile.skills
        ]

        # Education summary (first record)
        edu_summary: str | None = None
        if profile.educations:
            e = profile.educations[0]
            parts = [p for p in [e.degree, e.institution] if p]
            edu_summary = " – ".join(parts) if parts else None

        # AI summary snippet from cache
        ai_snippet: str | None = None
        ai_row = await db.scalar(
            select(AISummary).where(
                AISummary.entity_id == profile.id,
                AISummary.summary_type == SummaryType.RESUME_SUMMARY,
            )
        )
        if ai_row and isinstance(ai_row.content, dict):
            raw = ai_row.content.get("summary", "")
            ai_snippet = str(raw)[:150] if raw else None

        # AI match score for this job (if requested)
        match_score: int | None = None
        if filters.job_id:
            app_row = await db.scalar(
                select(Application).where(
                    Application.job_id == filters.job_id,
                    Application.candidate_id == profile.id,
                )
            )
            if app_row:
                ms_row = await db.scalar(
                    select(AISummary).where(
                        AISummary.entity_id == app_row.id,
                        AISummary.summary_type == SummaryType.MATCH_SCORE,
                    )
                )
                if ms_row and isinstance(ms_row.content, dict):
                    match_score = ms_row.content.get("score")

        return CandidateSearchItem(
            id=str(profile.id),
            user_id=str(profile.user_id),
            full_name=profile.full_name,
            headline=profile.headline,
            location=profile.location,
            years_of_experience=profile.years_of_experience,
            profile_strength=profile.profile_strength,
            notice_period_days=profile.notice_period_days,
            desired_salary_min=profile.desired_salary_min,
            desired_salary_max=profile.desired_salary_max,
            open_to_remote=profile.open_to_remote,
            skills=skill_results,
            education_summary=edu_summary,
            last_active=profile.updated_at.isoformat() if profile.updated_at else None,
            match_score=match_score,
            ai_summary_snippet=ai_snippet,
            resume_filename=profile.resume_filename,
        )
