"""Pydantic v2 schemas for the job posting module."""
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.job import JobStatus, JobType, QuestionType


# ─── Shared base ──────────────────────────────────────────────────────────────
class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ─── Skills ───────────────────────────────────────────────────────────────────
class JobSkillCreate(_Base):
    skill_name: Annotated[str, Field(min_length=1, max_length=100)]
    is_required: bool = True


class JobSkillResponse(_Base):
    id: uuid.UUID
    skill_name: str
    is_required: bool


# ─── Questions ────────────────────────────────────────────────────────────────
class JobQuestionCreate(_Base):
    question_text: Annotated[str, Field(min_length=1)]
    question_type: QuestionType = QuestionType.TEXT
    options: list[str] | None = None
    is_required: bool = True
    display_order: int = 0

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[str] | None, info: object) -> list[str] | None:
        # options only relevant for multiple_choice
        if v is not None and len(v) < 2:
            raise ValueError("multiple_choice questions need at least 2 options")
        return v


class JobQuestionUpdate(_Base):
    question_text: str | None = None
    question_type: QuestionType | None = None
    options: list[str] | None = None
    is_required: bool | None = None
    display_order: int | None = None


class JobQuestionResponse(_Base):
    id: uuid.UUID
    question_text: str
    question_type: QuestionType
    options: list[str] | None
    is_required: bool
    display_order: int


class QuestionsReorderRequest(_Base):
    """List of question IDs in their new order (first = order 0)."""
    question_ids: list[uuid.UUID]


# ─── Pipeline stages ──────────────────────────────────────────────────────────
class PipelineStageCreate(_Base):
    stage_name: Annotated[str, Field(min_length=1, max_length=100)]
    color: str = "#6366f1"


class PipelineStageUpdate(_Base):
    stage_name: str | None = None
    color: str | None = None


class PipelineStageReorderItem(_Base):
    id: uuid.UUID
    stage_order: int


class PipelineStageResponse(_Base):
    id: uuid.UUID
    stage_name: str
    stage_order: int
    color: str
    is_default: bool


# ─── Job CRUD ─────────────────────────────────────────────────────────────────
class JobCreate(_Base):
    title: Annotated[str, Field(min_length=1, max_length=255)]
    description: str | None = None
    requirements: str | None = None
    location: str | None = None
    job_type: JobType = JobType.FULL_TIME
    department: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: Annotated[str, Field(min_length=3, max_length=3)] = "USD"
    experience_years_min: int | None = None
    experience_years_max: int | None = None
    deadline: datetime | None = None

    @field_validator("salary_max")
    @classmethod
    def salary_range_valid(cls, v: int | None, info: object) -> int | None:
        if v is not None:
            data = getattr(info, "data", {})
            sal_min = data.get("salary_min")
            if sal_min is not None and v < sal_min:
                raise ValueError("salary_max must be >= salary_min")
        return v


class JobUpdate(_Base):
    title: Annotated[str, Field(min_length=1, max_length=255)] | None = None
    description: str | None = None
    requirements: str | None = None
    location: str | None = None
    job_type: JobType | None = None
    department: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: Annotated[str, Field(min_length=3, max_length=3)] | None = None
    experience_years_min: int | None = None
    experience_years_max: int | None = None
    deadline: datetime | None = None


class JobStatusUpdateRequest(_Base):
    status: JobStatus


# ─── Job responses ────────────────────────────────────────────────────────────
class JobResponse(_Base):
    id: uuid.UUID
    title: str
    description: str | None
    requirements: str | None
    location: str | None
    job_type: JobType
    department: str | None
    salary_min: int | None
    salary_max: int | None
    currency: str
    experience_years_min: int | None
    experience_years_max: int | None
    status: JobStatus
    posted_by: uuid.UUID | None
    company_id: uuid.UUID | None
    published_at: datetime | None
    closed_at: datetime | None
    archived_at: datetime | None
    deadline: datetime | None
    views_count: int
    applications_count: int
    created_at: datetime
    updated_at: datetime
    skills: list[JobSkillResponse]
    questions: list[JobQuestionResponse]
    pipeline_stages: list[PipelineStageResponse]


class JobListItem(_Base):
    """Lightweight projection used in list endpoints."""
    id: uuid.UUID
    title: str
    location: str | None
    job_type: JobType
    department: str | None
    status: JobStatus
    views_count: int
    applications_count: int
    created_at: datetime
    published_at: datetime | None
    deadline: datetime | None
    skills: list[JobSkillResponse] = []


class JobListResponse(_Base):
    items: list[JobListItem]
    total: int
    page: int
    page_size: int


# ─── Analytics ────────────────────────────────────────────────────────────────
class JobCountByStatus(_Base):
    draft: int = 0
    active: int = 0
    paused: int = 0
    closed: int = 0


class JobCountByType(_Base):
    full_time: int = 0
    part_time: int = 0
    contract: int = 0
    internship: int = 0
    remote: int = 0


class AnalyticsSummary(_Base):
    total_jobs: int
    active_jobs: int
    total_applications: int
    total_views: int
    by_status: JobCountByStatus
    by_type: JobCountByType
    top_jobs: list[JobListItem]
