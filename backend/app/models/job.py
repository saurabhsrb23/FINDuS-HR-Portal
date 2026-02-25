"""Job-related SQLAlchemy models: Job, JobSkill, JobQuestion, PipelineStage."""
import uuid
from datetime import datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JobStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class JobType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    REMOTE = "remote"


class QuestionType(str, Enum):
    TEXT = "text"
    YES_NO = "yes_no"
    MULTIPLE_CHOICE = "multiple_choice"
    RATING = "rating"


def _enum_values(obj):  # type: ignore[return]
    return [e.value for e in obj]


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        default=uuid.uuid4, server_default=sa.text("gen_random_uuid()"),
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_type: Mapped[JobType] = mapped_column(
        SAEnum(JobType, name="job_type_enum", create_type=False, values_callable=_enum_values),
        nullable=False, default=JobType.FULL_TIME, server_default=JobType.FULL_TIME.value,
    )
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")
    experience_years_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_years_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus, name="job_status_enum", create_type=False, values_callable=_enum_values),
        nullable=False, default=JobStatus.DRAFT, server_default=JobStatus.DRAFT.value,
    )
    posted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    views_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    applications_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa.func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=sa.func.now(), onupdate=sa.func.now(),
    )

    skills: Mapped[list["JobSkill"]] = relationship(
        "JobSkill", back_populates="job", cascade="all, delete-orphan", lazy="selectin",
    )
    questions: Mapped[list["JobQuestion"]] = relationship(
        "JobQuestion", back_populates="job", cascade="all, delete-orphan",
        order_by="JobQuestion.display_order", lazy="selectin",
    )
    pipeline_stages: Mapped[list["PipelineStage"]] = relationship(
        "PipelineStage", back_populates="job", cascade="all, delete-orphan",
        order_by="PipelineStage.stage_order", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Job id={self.id} title={self.title!r} status={self.status}>"


class JobSkill(Base):
    __tablename__ = "job_skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        default=uuid.uuid4, server_default=sa.text("gen_random_uuid()"),
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False,
    )
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sa.text("true"),
    )

    job: Mapped["Job"] = relationship("Job", back_populates="skills")


class JobQuestion(Base):
    __tablename__ = "job_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        default=uuid.uuid4, server_default=sa.text("gen_random_uuid()"),
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(
        SAEnum(QuestionType, name="question_type_enum", create_type=False,
               values_callable=_enum_values),
        nullable=False, default=QuestionType.TEXT, server_default=QuestionType.TEXT.value,
    )
    options: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    is_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sa.text("true"),
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    job: Mapped["Job"] = relationship("Job", back_populates="questions")


class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True,
        default=uuid.uuid4, server_default=sa.text("gen_random_uuid()"),
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False,
    )
    stage_name: Mapped[str] = mapped_column(String(100), nullable=False)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    color: Mapped[str] = mapped_column(String(7), nullable=False, server_default="#6366f1")
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=sa.text("false"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa.func.now(),
    )

    job: Mapped["Job"] = relationship("Job", back_populates="pipeline_stages")
