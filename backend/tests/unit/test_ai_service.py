"""Unit tests for AI service — all Groq calls mocked."""
from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.ai_summary import AISummary, SummaryType
from app.models.candidate import CandidateProfile, CandidateSkill
from app.models.application import Application, ApplicationStatus
from app.models.job import Job, JobStatus
from app.schemas.ai import (
    ChatRequest,
    ChatMessage,
    CompareRequest,
    GenerateJDRequest,
    RejectionEmailRequest,
)


# ── Groq mock response factory ────────────────────────────────────────────────

def _mock_groq_response(content: dict | str, tokens: int = 100):
    """Create a mock Groq API response."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = (
        json.dumps(content) if isinstance(content, dict) else content
    )
    mock_resp.usage.total_tokens = tokens
    return mock_resp


def _make_db():
    db = MagicMock()
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


def _make_profile(user_id: uuid.UUID | None = None) -> CandidateProfile:
    p = MagicMock(spec=CandidateProfile)
    p.id = uuid.uuid4()
    p.user_id = user_id or uuid.uuid4()
    p.headline = "Senior Python Developer"
    p.summary = "Experienced developer"
    p.skills = []
    p.work_experiences = []
    p.educations = []
    p.certifications = []
    p.projects = []
    p.years_of_experience = 5.0
    p.resume_url = "https://example.com/resume.pdf"
    p.desired_role = "Backend Engineer"
    return p


def _make_job() -> Job:
    j = MagicMock(spec=Job)
    j.id = uuid.uuid4()
    j.title = "Python Backend Engineer"
    j.description = "We need a Python developer"
    j.company_name = "TechCorp"
    j.skills = []
    j.status = JobStatus.ACTIVE
    j.experience_years_min = 3
    j.experience_years_max = 8
    return j


def _make_application(profile_id: uuid.UUID, job_id: uuid.UUID) -> Application:
    a = MagicMock(spec=Application)
    a.id = uuid.uuid4()
    a.candidate_id = profile_id
    a.job_id = job_id
    a.status = ApplicationStatus.APPLIED
    return a


# ── _call_groq ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_call_groq_success():
    from app.services.ai_service import _call_groq
    mock_resp = _mock_groq_response({"result": "ok"}, tokens=50)

    with patch("app.services.ai_service._get_groq") as mock_get_groq:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
        mock_get_groq.return_value = mock_client

        content, tokens = await _call_groq("test prompt")
        assert "result" in content
        assert tokens == 50


@pytest.mark.asyncio
async def test_call_groq_failure_raises_503():
    from app.services.ai_service import _call_groq

    with patch("app.services.ai_service._get_groq") as mock_get_groq:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))
        mock_get_groq.return_value = mock_client

        with pytest.raises(HTTPException) as exc:
            await _call_groq("test prompt")
        assert exc.value.status_code == 503


# ── get_resume_summary ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_resume_summary_cache_hit():
    from app.services.ai_service import get_resume_summary

    db = _make_db()
    candidate_id = uuid.uuid4()

    cached = MagicMock(spec=AISummary)
    cached.content = {
        "summary": "Great candidate",
        "strengths": ["Python", "FastAPI"],
        "experience_years": 5,
        "top_skills": ["Python", "SQL"],
    }

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = cached
    db.execute = AsyncMock(return_value=mock_result)

    result = await get_resume_summary(db, candidate_id, force_refresh=False)
    assert result.cached is True
    assert result.summary == "Great candidate"
    assert result.experience_years == 5


@pytest.mark.asyncio
async def test_get_resume_summary_generates_fresh():
    from app.services.ai_service import get_resume_summary

    db = _make_db()
    profile = _make_profile()

    ai_response = {
        "summary": "Experienced Python developer with 5 years.",
        "strengths": ["Python", "FastAPI", "PostgreSQL"],
        "experience_years": 5,
        "top_skills": ["Python", "FastAPI", "Docker"],
    }
    mock_groq = _mock_groq_response(ai_response, tokens=200)

    # First call (cache check) returns None, second call (profile load) returns profile
    results_sequence = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),   # cache miss
        MagicMock(scalar_one_or_none=MagicMock(return_value=profile)), # profile found
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),   # existing cache (upsert)
    ]
    db.execute = AsyncMock(side_effect=results_sequence)

    with patch("app.services.ai_service._get_groq") as mock_get_groq:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_groq)
        mock_get_groq.return_value = mock_client

        result = await get_resume_summary(db, profile.id, force_refresh=False)
        assert result.cached is False
        assert "Python" in result.summary or result.summary


@pytest.mark.asyncio
async def test_get_resume_summary_candidate_not_found():
    from app.services.ai_service import get_resume_summary

    db = _make_db()
    results_sequence = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # cache miss
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # profile not found
    ]
    db.execute = AsyncMock(side_effect=results_sequence)

    with pytest.raises(HTTPException) as exc:
        await get_resume_summary(db, uuid.uuid4(), force_refresh=False)
    assert exc.value.status_code == 404


# ── get_match_score ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_match_score_cache_hit():
    from app.services.ai_service import get_match_score

    db = _make_db()
    app_id = uuid.uuid4()

    cached = MagicMock(spec=AISummary)
    cached.content = {
        "score": 78,
        "grade": "B",
        "matched_skills": ["Python", "FastAPI"],
        "missing_skills": ["Docker"],
        "summary": "Good match overall.",
    }
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = cached
    db.execute = AsyncMock(return_value=mock_result)

    result = await get_match_score(db, app_id, force_refresh=False)
    assert result.cached is True
    assert result.score == 78
    assert result.grade == "B"


@pytest.mark.asyncio
async def test_get_match_score_fresh():
    from app.services.ai_service import get_match_score

    db = _make_db()
    profile = _make_profile()
    job = _make_job()
    app = _make_application(profile.id, job.id)

    ai_response = {
        "score": 85,
        "grade": "A",
        "matched_skills": ["Python", "FastAPI"],
        "missing_skills": [],
        "summary": "Excellent match.",
    }
    mock_groq = _mock_groq_response(ai_response, tokens=150)

    results = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # cache miss
        MagicMock(scalar_one_or_none=MagicMock(return_value=app)),    # app found
        MagicMock(scalar_one_or_none=MagicMock(return_value=job)),    # job found
        MagicMock(scalar_one_or_none=MagicMock(return_value=profile)),# profile found
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),   # cache upsert
    ]
    db.execute = AsyncMock(side_effect=results)

    with patch("app.services.ai_service._get_groq") as mock_get_groq:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_groq)
        mock_get_groq.return_value = mock_client

        result = await get_match_score(db, app.id, force_refresh=False)
        assert result.cached is False
        assert 0 <= result.score <= 100


@pytest.mark.asyncio
async def test_get_match_score_not_found():
    from app.services.ai_service import get_match_score

    db = _make_db()
    results = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # cache miss
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # app not found
    ]
    db.execute = AsyncMock(side_effect=results)

    with pytest.raises(HTTPException) as exc:
        await get_match_score(db, uuid.uuid4(), force_refresh=False)
    assert exc.value.status_code == 404


# ── generate_job_description ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_jd_success():
    from app.services.ai_service import generate_job_description

    db = _make_db()

    ai_response = {
        "title": "Senior Python Developer",
        "description": "We are looking for a senior Python developer...",
        "requirements": "5+ years Python\nFastAPI experience",
        "responsibilities": "Build backend APIs\nCode reviews",
        "benefits": "Remote work, competitive salary",
    }
    mock_groq = _mock_groq_response(ai_response, tokens=300)

    with patch("app.services.ai_service._get_groq") as mock_get_groq:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_groq)
        mock_get_groq.return_value = mock_client

        req = GenerateJDRequest(
            role="Python Developer",
            keywords=["FastAPI", "PostgreSQL"],
            experience_years=5,
        )
        result = await generate_job_description(db, req)
        assert result.title
        assert result.description


# ── draft_rejection_email ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_draft_rejection_email_success():
    from app.services.ai_service import draft_rejection_email

    db = _make_db()
    profile = _make_profile()
    job = _make_job()
    app = _make_application(profile.id, job.id)

    ai_response = {
        "subject": "Your Application Update",
        "body": "Dear Candidate,\n\nThank you for applying...",
    }
    mock_groq = _mock_groq_response(ai_response, tokens=150)

    results = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=app)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=job)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=profile)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # user lookup
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)),  # cache upsert
    ]
    db.execute = AsyncMock(side_effect=results)

    with patch("app.services.ai_service._get_groq") as mock_get_groq:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_groq)
        mock_get_groq.return_value = mock_client

        req = RejectionEmailRequest(application_id=app.id, reason="Looking for more experience")
        result = await draft_rejection_email(db, req)
        assert result.subject
        assert result.body


# ── optimize_resume ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_optimize_resume_cache_hit():
    from app.services.ai_service import optimize_resume

    db = _make_db()
    profile = _make_profile()

    cached_summary = MagicMock(spec=AISummary)
    cached_summary.content = {
        "overall_score": 72,
        "ats_score": 68,
        "impact_score": 75,
        "tips": ["Add more quantified achievements", "Include LinkedIn URL"],
        "strong_sections": ["Skills"],
        "weak_sections": ["Summary"],
    }

    results = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=profile)),        # profile found
        MagicMock(scalar_one_or_none=MagicMock(return_value=cached_summary)), # cache hit
    ]
    db.execute = AsyncMock(side_effect=results)

    result = await optimize_resume(db, profile.user_id, force_refresh=False)
    assert result.cached is True
    assert result.overall_score == 72
    assert len(result.tips) > 0


@pytest.mark.asyncio
async def test_optimize_resume_no_profile():
    from app.services.ai_service import optimize_resume

    db = _make_db()
    db.execute = AsyncMock(return_value=MagicMock(
        scalar_one_or_none=MagicMock(return_value=None)
    ))

    with pytest.raises(HTTPException) as exc:
        await optimize_resume(db, uuid.uuid4())
    assert exc.value.status_code == 404


# ── chatbot ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chat_success():
    from app.services.ai_service import chat

    db = _make_db()
    profile = _make_profile()
    mock_groq_resp = MagicMock()
    mock_groq_resp.choices = [MagicMock()]
    mock_groq_resp.choices[0].message.content = "Here are some interview tips..."
    mock_groq_resp.usage.total_tokens = 80

    db.execute = AsyncMock(return_value=MagicMock(
        scalar_one_or_none=MagicMock(return_value=profile)
    ))

    with patch("app.services.ai_service._get_groq") as mock_get_groq:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_groq_resp)
        mock_get_groq.return_value = mock_client

        req = ChatRequest(
            messages=[ChatMessage(role="user", content="How do I prepare for a Python interview?")]
        )
        result = await chat(db, profile.user_id, req)
        assert result.reply
        assert result.tokens_used == 80


@pytest.mark.asyncio
async def test_chat_groq_failure_raises_503():
    from app.services.ai_service import chat

    db = _make_db()
    profile = _make_profile()
    db.execute = AsyncMock(return_value=MagicMock(
        scalar_one_or_none=MagicMock(return_value=profile)
    ))

    with patch("app.services.ai_service._get_groq") as mock_get_groq:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Rate limit"))
        mock_get_groq.return_value = mock_client

        req = ChatRequest(
            messages=[ChatMessage(role="user", content="Help me")]
        )
        with pytest.raises(HTTPException) as exc:
            await chat(db, profile.user_id, req)
        assert exc.value.status_code == 503
