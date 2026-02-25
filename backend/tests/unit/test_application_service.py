"""Unit tests for ApplicationService."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.application import Application, ApplicationStatus, JobAlert
from app.models.candidate import CandidateProfile
from app.models.job import Job, JobStatus
from app.schemas.application import ApplyRequest, JobAlertCreate
from app.services.application_service import ApplicationService


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_profile(user_id: uuid.UUID | None = None) -> CandidateProfile:
    p = MagicMock(spec=CandidateProfile)
    p.id = uuid.uuid4()
    p.user_id = user_id or uuid.uuid4()
    p.resume_url = None
    p.skills = []
    return p


def _make_job(status: JobStatus = JobStatus.ACTIVE) -> Job:
    j = MagicMock(spec=Job)
    j.id = uuid.uuid4()
    j.title = "Software Engineer"
    j.company_name = "Acme Corp"
    j.location = "Bangalore"
    j.status = status
    j.created_at = datetime.now(timezone.utc)
    j.salary_max = 2000000
    return j


def _make_application(candidate_id: uuid.UUID | None = None, job_id: uuid.UUID | None = None) -> Application:
    a = MagicMock(spec=Application)
    a.id = uuid.uuid4()
    a.candidate_id = candidate_id or uuid.uuid4()
    a.job_id = job_id or uuid.uuid4()
    a.status = ApplicationStatus.APPLIED
    a.applied_at = datetime.now(timezone.utc)
    a.updated_at = datetime.now(timezone.utc)
    a.timeline = [{"status": "applied", "timestamp": datetime.now(timezone.utc).isoformat(), "note": ""}]
    a.answers = []
    a.cover_letter = None
    a.resume_url = None
    return a


def _make_svc(db: MagicMock) -> ApplicationService:
    return ApplicationService(db)


# ── Apply tests ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_apply_success():
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    profile = _make_profile()
    job = _make_job()
    app = _make_application(candidate_id=profile.id, job_id=job.id)

    svc = _make_svc(db)
    svc._candidate_repo = MagicMock()
    svc._candidate_repo.get_by_user_id = AsyncMock(return_value=profile)
    svc._repo = MagicMock()
    svc._repo.get_by_job_and_candidate = AsyncMock(return_value=None)
    svc._repo.create = AsyncMock(return_value=app)

    # Mock job lookup
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = job
    db.execute = AsyncMock(return_value=mock_result)

    data = ApplyRequest(cover_letter="I am interested")
    result = await svc.apply(profile.user_id, job.id, data)
    assert result.id == app.id
    svc._repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_apply_no_profile_raises():
    db = MagicMock()
    svc = _make_svc(db)
    svc._candidate_repo = MagicMock()
    svc._candidate_repo.get_by_user_id = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await svc.apply(uuid.uuid4(), uuid.uuid4(), ApplyRequest())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_apply_job_not_active_raises():
    db = MagicMock()
    profile = _make_profile()
    job = _make_job(status=JobStatus.PAUSED)

    svc = _make_svc(db)
    svc._candidate_repo = MagicMock()
    svc._candidate_repo.get_by_user_id = AsyncMock(return_value=profile)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = job
    db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc:
        await svc.apply(profile.user_id, job.id, ApplyRequest())
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_apply_duplicate_raises():
    db = MagicMock()
    profile = _make_profile()
    job = _make_job()
    existing_app = _make_application(candidate_id=profile.id, job_id=job.id)

    svc = _make_svc(db)
    svc._candidate_repo = MagicMock()
    svc._candidate_repo.get_by_user_id = AsyncMock(return_value=profile)
    svc._repo = MagicMock()
    svc._repo.get_by_job_and_candidate = AsyncMock(return_value=existing_app)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = job
    db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(HTTPException) as exc:
        await svc.apply(profile.user_id, job.id, ApplyRequest())
    assert exc.value.status_code == 409


# ── Withdraw tests ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_withdraw_success():
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    profile = _make_profile()
    app = _make_application(candidate_id=profile.id)
    app.status = ApplicationStatus.APPLIED
    withdrawn_app = _make_application(candidate_id=profile.id)
    withdrawn_app.status = ApplicationStatus.WITHDRAWN

    svc = _make_svc(db)
    svc._candidate_repo = MagicMock()
    svc._candidate_repo.get_by_user_id = AsyncMock(return_value=profile)
    svc._repo = MagicMock()
    svc._repo.get_by_id = AsyncMock(return_value=app)
    svc._repo.withdraw = AsyncMock(return_value=withdrawn_app)

    result = await svc.withdraw(profile.user_id, app.id)
    assert result.status == ApplicationStatus.WITHDRAWN


@pytest.mark.asyncio
async def test_withdraw_already_withdrawn_raises():
    db = MagicMock()
    profile = _make_profile()
    app = _make_application(candidate_id=profile.id)
    app.status = ApplicationStatus.WITHDRAWN

    svc = _make_svc(db)
    svc._candidate_repo = MagicMock()
    svc._candidate_repo.get_by_user_id = AsyncMock(return_value=profile)
    svc._repo = MagicMock()
    svc._repo.get_by_id = AsyncMock(return_value=app)

    with pytest.raises(HTTPException) as exc:
        await svc.withdraw(profile.user_id, app.id)
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_withdraw_not_owner_raises():
    db = MagicMock()
    profile = _make_profile()
    other_app = _make_application()  # different candidate_id

    svc = _make_svc(db)
    svc._candidate_repo = MagicMock()
    svc._candidate_repo.get_by_user_id = AsyncMock(return_value=profile)
    svc._repo = MagicMock()
    svc._repo.get_by_id = AsyncMock(return_value=other_app)

    with pytest.raises(HTTPException) as exc:
        await svc.withdraw(profile.user_id, other_app.id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_withdraw_hired_raises():
    db = MagicMock()
    profile = _make_profile()
    app = _make_application(candidate_id=profile.id)
    app.status = ApplicationStatus.HIRED

    svc = _make_svc(db)
    svc._candidate_repo = MagicMock()
    svc._candidate_repo.get_by_user_id = AsyncMock(return_value=profile)
    svc._repo = MagicMock()
    svc._repo.get_by_id = AsyncMock(return_value=app)

    with pytest.raises(HTTPException) as exc:
        await svc.withdraw(profile.user_id, app.id)
    assert exc.value.status_code == 422


# ── My applications tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_my_applications_empty_when_no_profile():
    db = MagicMock()
    svc = _make_svc(db)
    svc._candidate_repo = MagicMock()
    svc._candidate_repo.get_by_user_id = AsyncMock(return_value=None)

    result = await svc.get_my_applications(uuid.uuid4())
    assert result == []


@pytest.mark.asyncio
async def test_get_my_applications_returns_list():
    db = MagicMock()
    profile = _make_profile()
    job = _make_job()
    app = _make_application(candidate_id=profile.id, job_id=job.id)

    svc = _make_svc(db)
    svc._candidate_repo = MagicMock()
    svc._candidate_repo.get_by_user_id = AsyncMock(return_value=profile)
    svc._repo = MagicMock()
    svc._repo.get_by_candidate = AsyncMock(return_value=[app])

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = job
    db.execute = AsyncMock(return_value=mock_result)

    result = await svc.get_my_applications(profile.user_id)
    assert len(result) == 1
    assert result[0].job_id == app.job_id


# ── Salary benchmark tests ────────────────────────────────────────────────────

def test_salary_benchmark_no_filter():
    db = MagicMock()
    svc = _make_svc(db)
    result = svc.get_salary_benchmark()
    assert len(result) > 0
    assert result[0].min_salary > 0


def test_salary_benchmark_filter_by_role():
    db = MagicMock()
    svc = _make_svc(db)
    result = svc.get_salary_benchmark(role="Data Scientist")
    assert all("Data Scientist" in r.role for r in result)


def test_salary_benchmark_filter_by_location():
    db = MagicMock()
    svc = _make_svc(db)
    result = svc.get_salary_benchmark(location="Bangalore")
    assert all("Bangalore" in r.location for r in result)


def test_salary_benchmark_unknown_role_returns_fallback():
    db = MagicMock()
    svc = _make_svc(db)
    result = svc.get_salary_benchmark(role="Unicorn Wizard")
    # Falls back to first 5 entries
    assert len(result) == 5


# ── Alert tests ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_alert_success():
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    profile = _make_profile()
    alert = MagicMock(spec=JobAlert)
    alert.id = uuid.uuid4()
    alert.title = "Python Dev"

    svc = _make_svc(db)
    svc._candidate_repo = MagicMock()
    svc._candidate_repo.get_by_user_id = AsyncMock(return_value=profile)
    svc._repo = MagicMock()
    svc._repo.create_alert = AsyncMock(return_value=alert)

    data = JobAlertCreate(title="Python Dev", keywords="python,django")
    result = await svc.create_alert(profile.user_id, data)
    assert result.title == "Python Dev"


@pytest.mark.asyncio
async def test_delete_alert_success():
    db = MagicMock()
    db.commit = AsyncMock()

    profile = _make_profile()
    alert = MagicMock(spec=JobAlert)
    alert.id = uuid.uuid4()
    alert.candidate_id = profile.id

    svc = _make_svc(db)
    svc._candidate_repo = MagicMock()
    svc._candidate_repo.get_by_user_id = AsyncMock(return_value=profile)
    svc._repo = MagicMock()
    svc._repo.get_alert_by_id = AsyncMock(return_value=alert)
    svc._repo.delete_alert = AsyncMock()

    await svc.delete_alert(profile.user_id, alert.id)
    svc._repo.delete_alert.assert_called_once_with(alert)


@pytest.mark.asyncio
async def test_delete_alert_not_owner_raises():
    db = MagicMock()
    profile = _make_profile()
    alert = MagicMock(spec=JobAlert)
    alert.id = uuid.uuid4()
    alert.candidate_id = uuid.uuid4()  # different owner

    svc = _make_svc(db)
    svc._candidate_repo = MagicMock()
    svc._candidate_repo.get_by_user_id = AsyncMock(return_value=profile)
    svc._repo = MagicMock()
    svc._repo.get_alert_by_id = AsyncMock(return_value=alert)

    with pytest.raises(HTTPException) as exc:
        await svc.delete_alert(profile.user_id, alert.id)
    assert exc.value.status_code == 404
