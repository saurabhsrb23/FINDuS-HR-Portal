"""AI service — all Groq-powered operations with DB caching."""
from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

import structlog
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai_summary import AISummary, SummaryType
from app.models.application import Application
from app.models.candidate import CandidateProfile
from app.models.job import Job
from app.models.user import User
from app.schemas.ai import (
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

log = structlog.get_logger("donehr.ai_service")

_GROQ_MODEL_FAST = "llama-3.1-8b-instant"
_GROQ_MODEL_SMART = "llama-3.3-70b-versatile"

# ── Groq client (lazy init) ───────────────────────────────────────────────────

_groq_client = None


def _get_groq():
    global _groq_client
    if _groq_client is None:
        try:
            from groq import AsyncGroq
            key = settings.GROQ_API_KEY.get_secret_value() if settings.GROQ_API_KEY else ""
            if not key:
                raise ValueError("GROQ_API_KEY not set")
            _groq_client = AsyncGroq(api_key=key)
        except ImportError:
            raise HTTPException(status_code=503, detail="AI service not available (groq package missing).")
    return _groq_client


async def _call_groq(
    prompt: str,
    system: str = "You are a helpful HR assistant. Always respond with valid JSON.",
    model: str = _GROQ_MODEL_FAST,
    max_tokens: int = 1024,
) -> tuple[str, int]:
    """Call Groq API and return (content, token_usage). Raises 503 on failure."""
    try:
        client = _get_groq()
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return content, tokens
    except HTTPException:
        raise
    except Exception as exc:
        log.error("groq_call_failed", error=str(exc))
        raise HTTPException(status_code=503, detail=f"AI service temporarily unavailable: {str(exc)}")


def _parse_json_safe(text: str) -> dict:
    """Extract JSON from potentially markdown-wrapped response."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


# ── Cache helpers ─────────────────────────────────────────────────────────────

async def _get_cached(
    db: AsyncSession,
    entity_id: uuid.UUID,
    summary_type: SummaryType,
) -> AISummary | None:
    result = await db.execute(
        select(AISummary).where(
            AISummary.entity_id == entity_id,
            AISummary.summary_type == summary_type,
        )
    )
    return result.scalar_one_or_none()


async def _upsert_cache(
    db: AsyncSession,
    entity_id: uuid.UUID,
    entity_type: str,
    summary_type: SummaryType,
    content: dict,
    model_used: str,
    token_usage: int,
) -> AISummary:
    existing = await _get_cached(db, entity_id, summary_type)
    if existing:
        existing.content = content
        existing.model_used = model_used
        existing.token_usage = token_usage
        existing.updated_at = datetime.now(timezone.utc)
    else:
        existing = AISummary(
            entity_id=entity_id,
            entity_type=entity_type,
            summary_type=summary_type,
            content=content,
            model_used=model_used,
            token_usage=token_usage,
        )
        db.add(existing)
    await db.flush()
    await db.refresh(existing)
    return existing


# ── Resume Parser ─────────────────────────────────────────────────────────────

async def parse_resume_pdf(
    db: AsyncSession,
    user_id: uuid.UUID,
    pdf_bytes: bytes,
) -> ParsedResumeFields:
    """Extract structured profile data from PDF resume text."""
    try:
        import pdfplumber
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            text = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            ).strip()
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Failed to read PDF: {exc}")

    if not text:
        raise HTTPException(status_code=422, detail="PDF has no extractable text.")

    prompt = f"""Extract structured resume data from this resume text. Return ONLY valid JSON.

Resume text:
{text[:4000]}

Return JSON with these exact keys:
{{
  "full_name": "string or null",
  "phone": "string or null",
  "location": "city/country or null",
  "headline": "one-line professional title or null",
  "summary": "2-3 sentence professional summary or null",
  "years_of_experience": number or null,
  "skills": ["skill1", "skill2"],
  "work_experiences": [
    {{
      "company_name": "...",
      "job_title": "...",
      "start_date": "YYYY-MM-DD or null",
      "end_date": "YYYY-MM-DD or null",
      "is_current": false,
      "description": "brief description"
    }}
  ],
  "educations": [
    {{
      "institution": "...",
      "degree": "...",
      "field_of_study": "...",
      "start_year": number or null,
      "end_year": number or null
    }}
  ]
}}"""

    raw, tokens = await _call_groq(prompt, max_tokens=2048)
    data = _parse_json_safe(raw)

    # Cache the parsed result
    result_obj = await _get_cached(db, user_id, SummaryType.PARSED_RESUME)
    candidate_result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == user_id)
    )
    profile = candidate_result.scalar_one_or_none()
    if profile:
        await _upsert_cache(
            db, profile.id, "candidate", SummaryType.PARSED_RESUME, data,
            _GROQ_MODEL_FAST, tokens
        )
        await db.commit()

    return ParsedResumeFields(
        full_name=data.get("full_name"),
        phone=data.get("phone"),
        location=data.get("location"),
        headline=data.get("headline"),
        summary=data.get("summary"),
        years_of_experience=data.get("years_of_experience"),
        skills=data.get("skills", []),
        work_experiences=data.get("work_experiences", []),
        educations=data.get("educations", []),
    )


# ── Resume Summary (HR view) ──────────────────────────────────────────────────

async def get_resume_summary(
    db: AsyncSession,
    candidate_id: uuid.UUID,
    force_refresh: bool = False,
) -> ResumeSummaryResponse:
    """Generate/return cached 4-line candidate summary for HR."""
    if not force_refresh:
        cached = await _get_cached(db, candidate_id, SummaryType.RESUME_SUMMARY)
        if cached:
            c = cached.content
            return ResumeSummaryResponse(
                candidate_id=candidate_id,
                summary=c.get("summary", ""),
                strengths=c.get("strengths", []),
                experience_years=c.get("experience_years"),
                top_skills=c.get("top_skills", []),
                cached=True,
            )

    # Load candidate profile
    result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.id == candidate_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # Build context
    skills = ", ".join(s.skill_name for s in (profile.skills or [])[:10])
    exp_titles = ", ".join(
        f"{e.job_title} at {e.company_name}"
        for e in (profile.work_experiences or [])[:3]
    )
    edu = ", ".join(
        f"{e.degree} from {e.institution}"
        for e in (profile.educations or [])[:2]
    )

    prompt = f"""Create a concise HR-facing candidate summary. Return ONLY valid JSON.

Candidate info:
- Headline: {profile.headline or 'Not provided'}
- Summary: {profile.summary or 'Not provided'}
- Experience: {exp_titles or 'Not provided'}
- Education: {edu or 'Not provided'}
- Skills: {skills or 'Not provided'}
- Years of experience: {profile.years_of_experience or 'Unknown'}

Return JSON:
{{
  "summary": "4 concise sentences describing the candidate for HR",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "experience_years": number or null,
  "top_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"]
}}"""

    raw, tokens = await _call_groq(prompt, max_tokens=512)
    data = _parse_json_safe(raw)

    await _upsert_cache(
        db, candidate_id, "candidate", SummaryType.RESUME_SUMMARY,
        data, _GROQ_MODEL_FAST, tokens
    )
    await db.commit()

    return ResumeSummaryResponse(
        candidate_id=candidate_id,
        summary=data.get("summary", "Summary not available."),
        strengths=data.get("strengths", []),
        experience_years=data.get("experience_years"),
        top_skills=data.get("top_skills", []),
        cached=False,
    )


# ── Match Score ───────────────────────────────────────────────────────────────

async def get_match_score(
    db: AsyncSession,
    application_id: uuid.UUID,
    force_refresh: bool = False,
) -> MatchScoreResponse:
    """Calculate/return cached job-candidate match score."""
    if not force_refresh:
        cached = await _get_cached(db, application_id, SummaryType.MATCH_SCORE)
        if cached:
            c = cached.content
            return MatchScoreResponse(
                application_id=application_id,
                score=c.get("score", 0),
                grade=c.get("grade", "F"),
                matched_skills=c.get("matched_skills", []),
                missing_skills=c.get("missing_skills", []),
                summary=c.get("summary", ""),
                cached=True,
            )

    # Load application + job + candidate
    app_result = await db.execute(
        select(Application).where(Application.id == application_id)
    )
    app = app_result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    job_result = await db.execute(select(Job).where(Job.id == app.job_id))
    job = job_result.scalar_one_or_none()

    profile_result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.id == app.candidate_id)
    )
    profile = profile_result.scalar_one_or_none()

    if not job or not profile:
        raise HTTPException(status_code=404, detail="Job or candidate not found.")

    candidate_skills = ", ".join(s.skill_name for s in (profile.skills or []))
    job_skills = ", ".join(s.skill_name for s in (job.skills or []))

    prompt = f"""Score how well this candidate matches the job. Return ONLY valid JSON.

Job: {job.title}
Job description: {(job.description or '')[:500]}
Required skills: {job_skills or 'Not specified'}
Required experience: {job.experience_years_min or 0}-{job.experience_years_max or 'any'} years

Candidate headline: {profile.headline or 'Not provided'}
Candidate skills: {candidate_skills or 'Not provided'}
Candidate years of experience: {profile.years_of_experience or 'Unknown'}

Return JSON:
{{
  "score": integer 0-100,
  "grade": "A" or "B" or "C" or "D" or "F",
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3", "skill4"],
  "summary": "1-2 sentence match verdict"
}}"""

    raw, tokens = await _call_groq(prompt, max_tokens=512)
    data = _parse_json_safe(raw)
    data["score"] = max(0, min(100, int(data.get("score", 0))))

    await _upsert_cache(
        db, application_id, "application", SummaryType.MATCH_SCORE,
        data, _GROQ_MODEL_FAST, tokens
    )
    await db.commit()

    return MatchScoreResponse(
        application_id=application_id,
        score=data["score"],
        grade=data.get("grade", "F"),
        matched_skills=data.get("matched_skills", []),
        missing_skills=data.get("missing_skills", []),
        summary=data.get("summary", ""),
        cached=False,
    )


# ── Candidate Comparison ──────────────────────────────────────────────────────

async def compare_candidates(
    db: AsyncSession,
    application_ids: list[uuid.UUID],
) -> CandidateComparisonResponse:
    """Compare 2-3 candidates side-by-side."""
    if not 2 <= len(application_ids) <= 3:
        raise HTTPException(status_code=422, detail="Compare 2 or 3 candidates.")

    candidates_info = []
    for app_id in application_ids:
        app_result = await db.execute(
            select(Application).where(Application.id == app_id)
        )
        app = app_result.scalar_one_or_none()
        if not app:
            continue

        profile_result = await db.execute(
            select(CandidateProfile).where(CandidateProfile.id == app.candidate_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            continue

        user_result = await db.execute(
            select(User).where(User.id == profile.user_id)
        )
        user = user_result.scalar_one_or_none()

        skills = ", ".join(s.skill_name for s in (profile.skills or [])[:8])
        exp_count = len(profile.work_experiences or [])
        candidates_info.append(
            f"Candidate {len(candidates_info)+1} ({user.email if user else 'unknown'}):\n"
            f"- Headline: {profile.headline or 'N/A'}\n"
            f"- Skills: {skills or 'N/A'}\n"
            f"- Experience entries: {exp_count}\n"
            f"- Years exp: {profile.years_of_experience or 'unknown'}"
        )

    if not candidates_info:
        raise HTTPException(status_code=404, detail="No valid candidates found.")

    prompt = f"""Compare these candidates for HR decision-making. Return ONLY valid JSON.

{chr(10).join(candidates_info)}

Return JSON:
{{
  "candidates": [
    {{
      "name": "Candidate 1 (email)",
      "score": integer 0-100,
      "top_skills": ["skill1", "skill2"],
      "pros": ["pro1", "pro2"],
      "cons": ["con1"]
    }}
  ],
  "recommendation": "Who to shortlist and why (2-3 sentences)"
}}"""

    raw, tokens = await _call_groq(prompt, model=_GROQ_MODEL_SMART, max_tokens=1024)
    data = _parse_json_safe(raw)

    return CandidateComparisonResponse(
        candidates=data.get("candidates", []),
        recommendation=data.get("recommendation", ""),
    )


# ── AI Auto Ranking ───────────────────────────────────────────────────────────

async def rank_applicants(
    db: AsyncSession,
    job_id: uuid.UUID,
) -> RankingResponse:
    """Rank all applicants for a job. Called by Celery task."""
    from app.models.application import Application as AppModel

    # Load job
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    # Load applications (non-withdrawn)
    apps_result = await db.execute(
        select(AppModel).where(
            AppModel.job_id == job_id,
            AppModel.status != "withdrawn",
        )
    )
    apps = list(apps_result.scalars().all())

    if not apps:
        return RankingResponse(job_id=job_id, ranked=[], total=0)

    # Build candidate summaries (max 10 to stay within token limit)
    summaries = []
    for app in apps[:10]:
        profile_result = await db.execute(
            select(CandidateProfile).where(CandidateProfile.id == app.candidate_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            continue
        skills = ", ".join(s.skill_name for s in (profile.skills or [])[:5])
        summaries.append(
            f"Application {app.id}: {profile.headline or 'N/A'}, "
            f"skills: {skills or 'none'}, "
            f"exp: {profile.years_of_experience or '?'} years"
        )

    job_skills = ", ".join(s.skill_name for s in (job.skills or []))
    prompt = f"""Rank these applicants for the job. Return ONLY valid JSON.

Job: {job.title}
Required skills: {job_skills or 'not specified'}

Applicants:
{chr(10).join(summaries)}

Return JSON:
{{
  "ranked": [
    {{
      "rank": 1,
      "application_id": "uuid string",
      "score": integer 0-100,
      "reason": "brief reason"
    }}
  ]
}}"""

    raw, tokens = await _call_groq(prompt, model=_GROQ_MODEL_SMART, max_tokens=1024)
    data = _parse_json_safe(raw)

    ranked = data.get("ranked", [])
    content = {"ranked": ranked, "total": len(apps)}
    await _upsert_cache(
        db, job_id, "job", SummaryType.RANKING, content, _GROQ_MODEL_SMART, tokens
    )
    await db.commit()

    return RankingResponse(job_id=job_id, ranked=ranked, total=len(apps))


# ── JD Generator ─────────────────────────────────────────────────────────────

async def generate_job_description(
    db: AsyncSession,
    data: GenerateJDRequest,
) -> GenerateJDResponse:
    """Generate a complete job description from role + keywords."""
    kw = ", ".join(data.keywords) if data.keywords else "not specified"
    prompt = f"""Write a complete job description. Return ONLY valid JSON.

Role: {data.role}
Department: {data.department or 'not specified'}
Key skills/keywords: {kw}
Experience required: {data.experience_years or 'open'} years
Location: {data.location or 'flexible'}
Job type: {data.job_type}

Return JSON:
{{
  "title": "exact job title",
  "description": "2-3 paragraph overview of the role",
  "requirements": "bullet list of requirements (use \\n for new lines)",
  "responsibilities": "bullet list of responsibilities (use \\n for new lines)",
  "benefits": "2-3 benefits"
}}"""

    raw, tokens = await _call_groq(prompt, model=_GROQ_MODEL_SMART, max_tokens=1500)
    d = _parse_json_safe(raw)

    return GenerateJDResponse(
        title=d.get("title", data.role),
        description=d.get("description", ""),
        requirements=d.get("requirements", ""),
        responsibilities=d.get("responsibilities", ""),
        benefits=d.get("benefits", ""),
    )


# ── Rejection Email Drafter ───────────────────────────────────────────────────

async def draft_rejection_email(
    db: AsyncSession,
    req: RejectionEmailRequest,
) -> RejectionEmailResponse:
    """Draft a professional rejection email."""
    app_result = await db.execute(
        select(Application).where(Application.id == req.application_id)
    )
    app = app_result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    job_result = await db.execute(select(Job).where(Job.id == app.job_id))
    job = job_result.scalar_one_or_none()

    profile_result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.id == app.candidate_id)
    )
    profile = profile_result.scalar_one_or_none()
    user_result = await db.execute(
        select(User).where(User.id == profile.user_id if profile else None)
    ) if profile else None

    candidate_name = profile.full_name if profile else "Candidate"
    job_title = job.title if job else "the position"
    company = job.company_name if job and job.company_name else "our company"

    prompt = f"""Write a professional, empathetic rejection email. Return ONLY valid JSON.

Candidate name: {candidate_name}
Job applied for: {job_title}
Company: {company}
HR notes/reason (if any): {req.reason or 'not specified'}

Return JSON:
{{
  "subject": "email subject line",
  "body": "full email body (use \\n for line breaks)"
}}"""

    raw, tokens = await _call_groq(prompt, max_tokens=512)
    d = _parse_json_safe(raw)

    # Cache it
    await _upsert_cache(
        db, req.application_id, "application", SummaryType.REJECTION_EMAIL,
        d, _GROQ_MODEL_FAST, tokens
    )
    await db.commit()

    return RejectionEmailResponse(
        subject=d.get("subject", f"Your application for {job_title}"),
        body=d.get("body", "Thank you for applying. We have decided to move forward with other candidates."),
    )


# ── Resume Optimizer (candidate) ──────────────────────────────────────────────

async def optimize_resume(
    db: AsyncSession,
    user_id: uuid.UUID,
    force_refresh: bool = False,
) -> ResumeOptimizerResponse:
    """Give the candidate actionable resume improvement tips."""
    profile_result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    if not force_refresh:
        cached = await _get_cached(db, profile.id, SummaryType.RESUME_OPTIMIZER)
        if cached:
            c = cached.content
            return ResumeOptimizerResponse(
                overall_score=c.get("overall_score", 0),
                ats_score=c.get("ats_score", 0),
                impact_score=c.get("impact_score", 0),
                tips=c.get("tips", []),
                strong_sections=c.get("strong_sections", []),
                weak_sections=c.get("weak_sections", []),
                cached=True,
            )

    skills = ", ".join(s.skill_name for s in (profile.skills or []))
    exp_count = len(profile.work_experiences or [])
    edu_count = len(profile.educations or [])
    has_resume = bool(profile.resume_url)
    has_summary = bool(profile.summary)

    prompt = f"""Evaluate this candidate's profile and give improvement tips. Return ONLY valid JSON.

Profile stats:
- Has resume uploaded: {has_resume}
- Has professional summary: {has_summary}
- Skills count: {len(profile.skills or [])} ({skills[:200]})
- Work experience entries: {exp_count}
- Education entries: {edu_count}
- Certifications: {len(profile.certifications or [])}
- Projects: {len(profile.projects or [])}
- Headline: {profile.headline or 'missing'}
- Years of experience: {profile.years_of_experience or 'not specified'}

Return JSON:
{{
  "overall_score": integer 0-100,
  "ats_score": integer 0-100,
  "impact_score": integer 0-100,
  "tips": ["actionable tip 1", "actionable tip 2", "tip 3", "tip 4", "tip 5"],
  "strong_sections": ["section name"],
  "weak_sections": ["section name"]
}}"""

    raw, tokens = await _call_groq(prompt, max_tokens=768)
    data = _parse_json_safe(raw)

    await _upsert_cache(
        db, profile.id, "candidate", SummaryType.RESUME_OPTIMIZER,
        data, _GROQ_MODEL_FAST, tokens
    )
    await db.commit()

    return ResumeOptimizerResponse(
        overall_score=max(0, min(100, int(data.get("overall_score", 0)))),
        ats_score=max(0, min(100, int(data.get("ats_score", 0)))),
        impact_score=max(0, min(100, int(data.get("impact_score", 0)))),
        tips=data.get("tips", []),
        strong_sections=data.get("strong_sections", []),
        weak_sections=data.get("weak_sections", []),
        cached=False,
    )


# ── Career Chatbot ────────────────────────────────────────────────────────────

async def chat(
    db: AsyncSession,
    user_id: uuid.UUID,
    req: ChatRequest,
) -> ChatResponse:
    """Career-focused chatbot with candidate context."""
    # Load candidate context
    profile_result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()

    context_lines = []
    if profile:
        if profile.headline:
            context_lines.append(f"Current role/headline: {profile.headline}")
        if profile.skills:
            context_lines.append(f"Skills: {', '.join(s.skill_name for s in profile.skills[:10])}")
        if profile.years_of_experience:
            context_lines.append(f"Years of experience: {profile.years_of_experience}")
        if profile.desired_role:
            context_lines.append(f"Target role: {profile.desired_role}")
    if req.context:
        context_lines.append(req.context)

    context_str = "\n".join(context_lines) if context_lines else "No profile context available."

    system = f"""You are an AI career coach for DoneHR, helping candidates with:
- Resume writing and optimization
- Interview preparation
- Career growth advice
- Job search strategies
- Salary negotiation

Keep responses concise (2-4 paragraphs max), practical, and encouraging.

Candidate context:
{context_str}"""

    messages = [{"role": "system", "content": system}]
    for msg in req.messages[-10:]:  # last 10 messages for context window
        messages.append({"role": msg.role, "content": msg.content})

    try:
        client = _get_groq()
        response = await client.chat.completions.create(
            model=_GROQ_MODEL_FAST,
            messages=messages,
            temperature=0.7,
            max_tokens=512,
        )
        reply = response.choices[0].message.content or "I'm here to help with your career. What would you like to discuss?"
        tokens = response.usage.total_tokens if response.usage else 0
    except HTTPException:
        raise
    except Exception as exc:
        log.error("chatbot_failed", error=str(exc))
        raise HTTPException(status_code=503, detail="Chatbot temporarily unavailable.")

    return ChatResponse(reply=reply, tokens_used=tokens)
