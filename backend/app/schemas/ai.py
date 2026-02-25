"""Pydantic schemas for AI endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.ai_summary import SummaryType


# ── Shared ────────────────────────────────────────────────────────────────────

class AISummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_id: uuid.UUID
    entity_type: str
    summary_type: SummaryType
    content: dict
    model_used: str
    token_usage: int
    created_at: datetime


# ── Resume Parser ─────────────────────────────────────────────────────────────

class ParsedResumeFields(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    summary: str | None = None
    years_of_experience: float | None = None
    skills: list[str] = []
    work_experiences: list[dict] = []
    educations: list[dict] = []


# ── Resume Summary (HR view) ──────────────────────────────────────────────────

class ResumeSummaryResponse(BaseModel):
    candidate_id: uuid.UUID
    summary: str           # 4-line plain text
    strengths: list[str]   # top 3
    experience_years: float | None
    top_skills: list[str]
    cached: bool = False


# ── Match Score ───────────────────────────────────────────────────────────────

class MatchScoreResponse(BaseModel):
    application_id: uuid.UUID
    score: int             # 0-100
    grade: str             # A, B, C, D, F
    matched_skills: list[str]
    missing_skills: list[str]
    summary: str           # 1-2 sentence verdict
    cached: bool = False


# ── Candidate Comparison ──────────────────────────────────────────────────────

class CompareRequest(BaseModel):
    application_ids: list[uuid.UUID]


class CandidateComparisonResponse(BaseModel):
    candidates: list[dict]    # [{name, score, skills, pros, cons}]
    recommendation: str       # who to shortlist and why


# ── Ranking ───────────────────────────────────────────────────────────────────

class RankingResponse(BaseModel):
    job_id: uuid.UUID
    ranked: list[dict]    # [{rank, application_id, candidate_name, score, reason}]
    total: int


# ── JD Generator ─────────────────────────────────────────────────────────────

class GenerateJDRequest(BaseModel):
    role: str
    department: str | None = None
    keywords: list[str] = []
    experience_years: int | None = None
    location: str | None = None
    job_type: str = "full_time"


class GenerateJDResponse(BaseModel):
    title: str
    description: str
    requirements: str
    responsibilities: str
    benefits: str


# ── Rejection Email ───────────────────────────────────────────────────────────

class RejectionEmailRequest(BaseModel):
    application_id: uuid.UUID
    reason: str | None = None       # optional HR note


class RejectionEmailResponse(BaseModel):
    subject: str
    body: str


# ── Resume Optimizer ─────────────────────────────────────────────────────────

class ResumeOptimizerResponse(BaseModel):
    overall_score: int            # 0-100
    ats_score: int                # Applicant Tracking System compatibility
    impact_score: int             # how impactful the content is
    tips: list[str]               # actionable tips
    strong_sections: list[str]
    weak_sections: list[str]
    cached: bool = False


# ── Career Chatbot ────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str      # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    context: str | None = None   # optional context (e.g. current job title)


class ChatResponse(BaseModel):
    reply: str
    tokens_used: int
