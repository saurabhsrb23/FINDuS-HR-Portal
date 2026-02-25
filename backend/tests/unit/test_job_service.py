"""Unit tests for JobService — pure logic, DB calls mocked via AsyncMock."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.job import JobStatus, JobType, QuestionType
from app.models.user import UserRole
from app.schemas.job import (
    JobCreate,
    JobQuestionCreate,
    JobSkillCreate,
    JobUpdate,
    PipelineStageCreate,
    PipelineStageReorderItem,
    PipelineStageUpdate,
    QuestionsReorderRequest,
)
from app.services.job_service import JobService

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

NOW = datetime.now(timezone.utc)
JOB_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
HR_ROLE = UserRole.HR_ADMIN


def _mock_job(
    status: JobStatus = JobStatus.DRAFT,
    posted_by: uuid.UUID | None = None,
) -> MagicMock:
    job = MagicMock()
    job.id = JOB_ID
    job.title = "Backend Engineer"
    job.status = status
    job.posted_by = posted_by or USER_ID
    job.views_count = 0
    job.applications_count = 0
    job.skills = []
    job.questions = []
    job.pipeline_stages = []
    job.created_at = NOW
    job.updated_at = NOW
    job.published_at = None
    job.closed_at = None
    job.archived_at = None
    job.deadline = None
    return job


def _make_service() -> tuple[JobService, MagicMock]:
    """Return (service, mock_repo) pair."""
    db = AsyncMock()
    service = JobService(db)
    repo = AsyncMock()
    service._repo = repo  # type: ignore[attr-defined]
    return service, repo


# ──────────────────────────────────────────────────────────────────────────────
# create_job
# ──────────────────────────────────────────────────────────────────────────────

class TestCreateJob:
    @pytest.mark.asyncio
    async def test_creates_and_returns_job(self):
        service, repo = _make_service()
        job = _mock_job()
        repo.create.return_value = job

        data = JobCreate(title="Backend Engineer")
        result = await service.create_job(data, user_id=USER_ID)

        repo.create.assert_called_once_with(data, USER_ID)
        assert result is job

    @pytest.mark.asyncio
    async def test_create_sets_correct_user(self):
        service, repo = _make_service()
        other_user = uuid.uuid4()
        job = _mock_job()
        job.posted_by = other_user
        repo.create.return_value = job

        data = JobCreate(title="DevOps Engineer")
        await service.create_job(data, user_id=other_user)

        _, kwargs = repo.create.call_args
        assert kwargs.get("user_id") == other_user or repo.create.call_args[0][1] == other_user


# ──────────────────────────────────────────────────────────────────────────────
# get_job
# ──────────────────────────────────────────────────────────────────────────────

class TestGetJob:
    @pytest.mark.asyncio
    async def test_returns_job_when_found(self):
        service, repo = _make_service()
        job = _mock_job()
        repo.get_by_id.return_value = job

        result = await service.get_job(JOB_ID)

        repo.get_by_id.assert_called_once_with(JOB_ID)
        assert result is job

    @pytest.mark.asyncio
    async def test_raises_404_when_not_found(self):
        from fastapi import HTTPException

        service, repo = _make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await service.get_job(JOB_ID)

        assert exc_info.value.status_code == 404


# ──────────────────────────────────────────────────────────────────────────────
# update_job
# ──────────────────────────────────────────────────────────────────────────────

class TestUpdateJob:
    @pytest.mark.asyncio
    async def test_owner_can_update(self):
        service, repo = _make_service()
        job = _mock_job(posted_by=USER_ID)
        updated = _mock_job(posted_by=USER_ID)
        updated.title = "Updated Title"
        repo.get_by_id.return_value = job
        repo.update.return_value = updated

        data = JobUpdate(title="Updated Title")
        result = await service.update_job(JOB_ID, data, USER_ID, UserRole.HR)

        repo.update.assert_called_once_with(job, data)
        assert result is updated

    @pytest.mark.asyncio
    async def test_admin_can_update_any_job(self):
        service, repo = _make_service()
        other_user = uuid.uuid4()
        job = _mock_job(posted_by=other_user)
        repo.get_by_id.return_value = job
        repo.update.return_value = job

        data = JobUpdate(title="Admin Edit")
        # Should not raise
        await service.update_job(JOB_ID, data, USER_ID, UserRole.SUPERADMIN)

    @pytest.mark.asyncio
    async def test_non_owner_hr_cannot_update(self):
        from fastapi import HTTPException

        service, repo = _make_service()
        other_user = uuid.uuid4()
        job = _mock_job(posted_by=other_user)
        repo.get_by_id.return_value = job

        data = JobUpdate(title="Sneaky Edit")
        with pytest.raises(HTTPException) as exc_info:
            await service.update_job(JOB_ID, data, USER_ID, UserRole.HR)

        assert exc_info.value.status_code == 403


# ──────────────────────────────────────────────────────────────────────────────
# delete_job
# ──────────────────────────────────────────────────────────────────────────────

class TestDeleteJob:
    @pytest.mark.asyncio
    async def test_owner_can_delete_draft(self):
        service, repo = _make_service()
        job = _mock_job(status=JobStatus.DRAFT, posted_by=USER_ID)
        repo.get_by_id.return_value = job

        await service.delete_job(JOB_ID, USER_ID, UserRole.HR)

        repo.delete.assert_called_once_with(job)

    @pytest.mark.asyncio
    async def test_cannot_delete_active_job(self):
        from fastapi import HTTPException

        service, repo = _make_service()
        job = _mock_job(status=JobStatus.ACTIVE, posted_by=USER_ID)
        repo.get_by_id.return_value = job

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_job(JOB_ID, USER_ID, UserRole.HR)

        assert exc_info.value.status_code == 409


# ──────────────────────────────────────────────────────────────────────────────
# publish_job / pause_job / close_job
# ──────────────────────────────────────────────────────────────────────────────

class TestStatusTransitions:
    @pytest.mark.asyncio
    async def test_publish_draft_job(self):
        service, repo = _make_service()
        job = _mock_job(status=JobStatus.DRAFT, posted_by=USER_ID)
        published = _mock_job(status=JobStatus.ACTIVE, posted_by=USER_ID)
        repo.get_by_id.return_value = job
        repo.update.return_value = published

        result = await service.publish_job(JOB_ID, USER_ID, HR_ROLE)

        assert result.status == JobStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_cannot_publish_closed_job(self):
        from fastapi import HTTPException

        service, repo = _make_service()
        job = _mock_job(status=JobStatus.CLOSED, posted_by=USER_ID)
        repo.get_by_id.return_value = job

        with pytest.raises(HTTPException) as exc_info:
            await service.publish_job(JOB_ID, USER_ID, HR_ROLE)

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_pause_active_job(self):
        service, repo = _make_service()
        job = _mock_job(status=JobStatus.ACTIVE, posted_by=USER_ID)
        paused = _mock_job(status=JobStatus.PAUSED, posted_by=USER_ID)
        repo.get_by_id.return_value = job
        repo.update.return_value = paused

        result = await service.pause_job(JOB_ID, USER_ID, HR_ROLE)

        assert result.status == JobStatus.PAUSED

    @pytest.mark.asyncio
    async def test_cannot_pause_draft_job(self):
        from fastapi import HTTPException

        service, repo = _make_service()
        job = _mock_job(status=JobStatus.DRAFT, posted_by=USER_ID)
        repo.get_by_id.return_value = job

        with pytest.raises(HTTPException) as exc_info:
            await service.pause_job(JOB_ID, USER_ID, HR_ROLE)

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_close_active_job(self):
        service, repo = _make_service()
        job = _mock_job(status=JobStatus.ACTIVE, posted_by=USER_ID)
        closed = _mock_job(status=JobStatus.CLOSED, posted_by=USER_ID)
        repo.get_by_id.return_value = job
        repo.update.return_value = closed

        result = await service.close_job(JOB_ID, USER_ID, HR_ROLE)

        assert result.status == JobStatus.CLOSED


# ──────────────────────────────────────────────────────────────────────────────
# clone_job
# ──────────────────────────────────────────────────────────────────────────────

class TestCloneJob:
    @pytest.mark.asyncio
    async def test_clone_creates_new_draft(self):
        service, repo = _make_service()
        original = _mock_job(status=JobStatus.ACTIVE, posted_by=USER_ID)
        clone = _mock_job(status=JobStatus.DRAFT)
        clone.id = uuid.uuid4()
        repo.get_by_id.return_value = original
        repo.create.return_value = clone

        result = await service.clone_job(JOB_ID, USER_ID)

        repo.create.assert_called_once()
        assert result.status == JobStatus.DRAFT
        assert result.id != JOB_ID


# ──────────────────────────────────────────────────────────────────────────────
# add_skill / remove_skill
# ──────────────────────────────────────────────────────────────────────────────

class TestSkills:
    @pytest.mark.asyncio
    async def test_add_skill_success(self):
        service, repo = _make_service()
        job = _mock_job(status=JobStatus.DRAFT, posted_by=USER_ID)
        skill = MagicMock()
        skill.id = uuid.uuid4()
        skill.skill_name = "Python"
        skill.is_required = True
        repo.get_by_id.return_value = job
        repo.add_skill.return_value = skill

        data = JobSkillCreate(skill_name="Python")
        result = await service.add_skill(JOB_ID, data, USER_ID, UserRole.HR)

        assert result is skill

    @pytest.mark.asyncio
    async def test_remove_skill_success(self):
        service, repo = _make_service()
        job = _mock_job(posted_by=USER_ID)
        skill = MagicMock()
        skill.id = uuid.uuid4()
        repo.get_by_id.return_value = job
        repo.remove_skill.return_value = None

        await service.remove_skill(JOB_ID, skill.id, USER_ID, UserRole.HR)

        repo.remove_skill.assert_called_once_with(job, skill.id)


# ──────────────────────────────────────────────────────────────────────────────
# questions
# ──────────────────────────────────────────────────────────────────────────────

class TestQuestions:
    @pytest.mark.asyncio
    async def test_create_text_question(self):
        service, repo = _make_service()
        job = _mock_job(status=JobStatus.DRAFT, posted_by=USER_ID)
        question = MagicMock()
        question.id = uuid.uuid4()
        question.question_text = "Tell me about yourself"
        question.question_type = QuestionType.TEXT
        repo.get_by_id.return_value = job
        repo.add_question.return_value = question

        data = JobQuestionCreate(question_text="Tell me about yourself")
        result = await service.create_question(JOB_ID, data, USER_ID, UserRole.HR)

        assert result is question

    @pytest.mark.asyncio
    async def test_delete_question(self):
        service, repo = _make_service()
        job = _mock_job(posted_by=USER_ID)
        q_id = uuid.uuid4()
        question = MagicMock()
        question.id = q_id
        repo.get_by_id.return_value = job
        repo.get_question.return_value = question

        await service.delete_question(JOB_ID, q_id, USER_ID, UserRole.HR)

        repo.delete_question.assert_called_once_with(question)

    @pytest.mark.asyncio
    async def test_reorder_questions(self):
        service, repo = _make_service()
        job = _mock_job(posted_by=USER_ID)
        q1, q2 = uuid.uuid4(), uuid.uuid4()
        reordered = [MagicMock(), MagicMock()]
        repo.get_by_id.return_value = job
        repo.reorder_questions.return_value = reordered

        payload = QuestionsReorderRequest(question_ids=[q1, q2])
        result = await service.reorder_questions(JOB_ID, payload, USER_ID, UserRole.HR)

        assert result == reordered


# ──────────────────────────────────────────────────────────────────────────────
# pipeline
# ──────────────────────────────────────────────────────────────────────────────

class TestPipeline:
    @pytest.mark.asyncio
    async def test_add_pipeline_stage(self):
        service, repo = _make_service()
        job = _mock_job(posted_by=USER_ID)
        stage = MagicMock()
        stage.id = uuid.uuid4()
        stage.stage_name = "Technical Round"
        repo.get_by_id.return_value = job
        repo.add_pipeline_stage.return_value = stage

        data = PipelineStageCreate(stage_name="Technical Round")
        result = await service.add_pipeline_stage(JOB_ID, data, USER_ID, UserRole.HR)

        assert result is stage

    @pytest.mark.asyncio
    async def test_delete_default_stage_blocked(self):
        from fastapi import HTTPException

        service, repo = _make_service()
        job = _mock_job(posted_by=USER_ID)
        stage_id = uuid.uuid4()
        stage = MagicMock()
        stage.id = stage_id
        stage.is_default = True
        repo.get_by_id.return_value = job
        repo.get_pipeline_stage.return_value = stage

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_pipeline_stage(JOB_ID, stage_id, USER_ID, UserRole.HR)

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_reorder_pipeline(self):
        service, repo = _make_service()
        job = _mock_job(posted_by=USER_ID)
        s1, s2 = uuid.uuid4(), uuid.uuid4()
        reordered = [MagicMock(), MagicMock()]
        repo.get_by_id.return_value = job
        repo.reorder_pipeline.return_value = reordered

        items = [
            PipelineStageReorderItem(id=s1, stage_order=0),
            PipelineStageReorderItem(id=s2, stage_order=1),
        ]
        result = await service.reorder_pipeline(JOB_ID, items, USER_ID, UserRole.HR)

        assert result == reordered


# ──────────────────────────────────────────────────────────────────────────────
# list_jobs
# ──────────────────────────────────────────────────────────────────────────────

class TestListJobs:
    @pytest.mark.asyncio
    async def test_list_returns_paginated_result(self):
        service, repo = _make_service()
        items = [_mock_job(), _mock_job()]
        repo.get_all.return_value = (items, 2)

        result = await service.list_jobs(
            user_id=USER_ID,
            role=UserRole.HR,
            status=None,
            job_type=None,
            search=None,
            page=1,
            page_size=20,
        )

        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1


# ──────────────────────────────────────────────────────────────────────────────
# analytics
# ──────────────────────────────────────────────────────────────────────────────

class TestAnalytics:
    @pytest.mark.asyncio
    async def test_analytics_summary_shape(self):
        service, repo = _make_service()
        repo.count_by_status.return_value = {
            "draft": 3, "active": 5, "paused": 1, "closed": 2,
        }
        repo.count_by_type.return_value = {
            "full_time": 8, "part_time": 2, "contract": 1, "internship": 0, "remote": 0,
        }
        repo.total_applications.return_value = 42
        repo.total_views.return_value = 1000
        repo.top_jobs.return_value = []

        result = await service.get_analytics_summary(USER_ID, UserRole.HR_ADMIN)

        assert result.total_jobs == 11  # 3+5+1+2
        assert result.active_jobs == 5
        assert result.total_applications == 42
        assert result.total_views == 1000
        assert result.by_status.draft == 3
        assert result.by_type.full_time == 8
