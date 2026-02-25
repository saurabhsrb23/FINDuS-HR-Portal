"""Search-related Pydantic schemas for Module 6."""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class SortBy(str, Enum):
    RELEVANCE = "relevance"
    EXPERIENCE = "experience"
    MATCH_SCORE = "match_score"
    RECENTLY_ACTIVE = "recently_active"
    PROFILE_STRENGTH = "profile_strength"


class SkillMatchMode(str, Enum):
    AND = "AND"   # candidate must have ALL listed skills
    OR = "OR"    # candidate must have ANY listed skill


class EducationTier(str, Enum):
    ANY = "any"
    UNDERGRADUATE = "undergraduate"   # B.Tech / B.E. / B.Sc. / BCA
    POSTGRADUATE = "postgraduate"     # M.Tech / MBA / M.Sc.
    PHD = "phd"


class WorkPreference(str, Enum):
    ANY = "any"
    REMOTE = "remote"
    ONSITE = "onsite"
    HYBRID = "hybrid"


# ── Sub-schemas ────────────────────────────────────────────────────────────────

class SkillFilter(BaseModel):
    skill: str = Field(..., min_length=1, max_length=100)
    min_years: float | None = Field(default=None, ge=0, le=50)


# ── Main search request ───────────────────────────────────────────────────────

class SearchCandidateRequest(BaseModel):
    # Full-text / boolean query ("Python AND Django NOT PHP")
    query: str | None = Field(default=None, max_length=500)

    # Skill filters
    skills: list[SkillFilter] = Field(default_factory=list)
    skill_match: SkillMatchMode = SkillMatchMode.AND

    # Experience
    experience_min: float | None = Field(default=None, ge=0, le=60)
    experience_max: float | None = Field(default=None, ge=0, le=60)

    # Location
    location: str | None = Field(default=None, max_length=200)

    # Notice period
    notice_period_max_days: int | None = Field(default=None, ge=0, le=365)

    # CTC in INR lakhs (1 lakh = 100 000 INR)
    ctc_min: int | None = Field(default=None, ge=0)
    ctc_max: int | None = Field(default=None, ge=0)

    # Education
    education_tier: EducationTier = EducationTier.ANY

    # Profile quality
    profile_strength_min: int | None = Field(default=None, ge=0, le=100)

    # Work preference
    work_preference: WorkPreference = WorkPreference.ANY

    # Last active (within N days)
    last_active_days: int | None = Field(default=None, ge=1, le=365)

    # Per-job AI match score filter (HR-side applicant ranking)
    job_id: uuid.UUID | None = None
    match_score_min: int | None = Field(default=None, ge=0, le=100)

    # Pagination (cursor-based)
    cursor: str | None = None   # base64(updated_at.isoformat() + "|" + str(id))
    page_size: int = Field(default=20, ge=1, le=50)

    # Sort
    sort_by: SortBy = SortBy.RELEVANCE


# ── Response schemas ──────────────────────────────────────────────────────────

class SkillResult(BaseModel):
    skill_name: str
    proficiency: int
    years_exp: float | None
    matched: bool = False          # True when this skill matched a filter


class CandidateSearchItem(BaseModel):
    id: str                        # candidate_profile.id
    user_id: str
    full_name: str | None
    headline: str | None
    location: str | None
    years_of_experience: float | None
    profile_strength: int
    notice_period_days: int | None
    desired_salary_min: int | None
    desired_salary_max: int | None
    open_to_remote: bool
    skills: list[SkillResult]
    education_summary: str | None  # "B.Tech – IIT Bombay"
    last_active: str | None        # ISO datetime
    match_score: int | None        # from AI if job_id provided
    ai_summary_snippet: str | None # first 150 chars of AI summary
    resume_filename: str | None


class SearchResult(BaseModel):
    total: int
    candidates: list[CandidateSearchItem]
    next_cursor: str | None
    page_size: int
    cached: bool = False


# ── Saved search ──────────────────────────────────────────────────────────────

class SavedSearchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    filters: dict[str, Any]


class SavedSearchResponse(BaseModel):
    id: str
    name: str
    filters: dict[str, Any]
    created_at: str


# ── Talent pool ───────────────────────────────────────────────────────────────

class TalentPoolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class TalentPoolAddCandidates(BaseModel):
    candidate_ids: list[str] = Field(..., min_length=1)
    notes: str | None = None


class TalentPoolResponse(BaseModel):
    id: str
    name: str
    candidate_count: int
    created_at: str


# ── Bulk export ───────────────────────────────────────────────────────────────

class BulkExportRequest(BaseModel):
    candidate_ids: list[str] = Field(..., min_length=1, max_length=100)
