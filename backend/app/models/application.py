"""Application and JobAlert models."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

_enum_values = lambda obj: [e.value for e in obj]  # noqa: E731


class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, name="application_status_enum", create_type=False, values_callable=_enum_values),
        default=ApplicationStatus.APPLIED,
    )
    cover_letter: Mapped[str | None] = mapped_column(Text)
    resume_url: Mapped[str | None] = mapped_column(String(500))

    # Timeline events stored as JSONB list: [{status, timestamp, note}]
    timeline: Mapped[list | None] = mapped_column(JSONB, default=list)

    # HR fields
    hr_notes: Mapped[str | None] = mapped_column(Text)
    pipeline_stage_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("pipeline_stages.id", ondelete="SET NULL"))
    rating: Mapped[int | None] = mapped_column(Integer)  # 1-5

    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    candidate: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="applications")  # type: ignore[name-defined]
    answers: Mapped[list["ApplicationAnswer"]] = relationship("ApplicationAnswer", back_populates="application", cascade="all, delete-orphan", lazy="selectin")


class ApplicationAnswer(Base):
    __tablename__ = "application_answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_questions.id", ondelete="CASCADE"), nullable=False)
    answer_text: Mapped[str | None] = mapped_column(Text)

    application: Mapped["Application"] = relationship("Application", back_populates="answers")


class JobAlert(Base):
    __tablename__ = "job_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    keywords: Mapped[str | None] = mapped_column(String(500))
    location: Mapped[str | None] = mapped_column(String(200))
    job_type: Mapped[str | None] = mapped_column(String(50))
    salary_min: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidate: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="job_alerts")  # type: ignore[name-defined]
