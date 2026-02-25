"""Candidate profile and related models."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Computed, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

_enum_values = lambda obj: [e.value for e in obj]  # noqa: E731


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Basic info
    full_name: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(20))
    location: Mapped[str | None] = mapped_column(String(200))
    headline: Mapped[str | None] = mapped_column(String(300))
    summary: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(String(500))

    # Resume — stored as base64 data URL (can be several hundred KB)
    resume_url: Mapped[str | None] = mapped_column(Text)
    resume_filename: Mapped[str | None] = mapped_column(String(255))
    resume_parsed_data: Mapped[dict | None] = mapped_column(JSONB)

    # Preferences
    desired_role: Mapped[str | None] = mapped_column(String(200))
    desired_salary_min: Mapped[int | None] = mapped_column(Integer)
    desired_salary_max: Mapped[int | None] = mapped_column(Integer)
    desired_location: Mapped[str | None] = mapped_column(String(200))
    open_to_remote: Mapped[bool] = mapped_column(Boolean, default=True)
    notice_period_days: Mapped[int | None] = mapped_column(Integer)
    years_of_experience: Mapped[float | None] = mapped_column(Float)

    # Profile strength 0-100
    profile_strength: Mapped[int] = mapped_column(Integer, default=0)

    # Full-text search vector — GENERATED ALWAYS AS STORED, managed by PostgreSQL
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('english', coalesce(headline, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(summary, '')), 'B') || "
            "setweight(to_tsvector('english', coalesce(desired_role, '')), 'C') || "
            "setweight(to_tsvector('english', coalesce(location, '')), 'D') || "
            "setweight(to_tsvector('english', coalesce(full_name, '')), 'D')",
            persisted=True,
        ),
        nullable=True,
        deferred=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    work_experiences: Mapped[list["WorkExperience"]] = relationship("WorkExperience", back_populates="candidate", cascade="all, delete-orphan", order_by="WorkExperience.start_date.desc()", lazy="selectin")
    educations: Mapped[list["Education"]] = relationship("Education", back_populates="candidate", cascade="all, delete-orphan", order_by="Education.start_year.desc()", lazy="selectin")
    certifications: Mapped[list["Certification"]] = relationship("Certification", back_populates="candidate", cascade="all, delete-orphan", lazy="selectin")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="candidate", cascade="all, delete-orphan", lazy="selectin")
    skills: Mapped[list["CandidateSkill"]] = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan", lazy="selectin")
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="candidate", lazy="dynamic")
    job_alerts: Mapped[list["JobAlert"]] = relationship("JobAlert", back_populates="candidate", cascade="all, delete-orphan", lazy="selectin")


class WorkExperience(Base):
    __tablename__ = "work_experiences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)

    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    job_title: Mapped[str] = mapped_column(String(200), nullable=False)
    employment_type: Mapped[EmploymentType] = mapped_column(SAEnum(EmploymentType, name="employment_type_enum", create_type=False, values_callable=_enum_values), default=EmploymentType.FULL_TIME)
    location: Mapped[str | None] = mapped_column(String(200))
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    description: Mapped[str | None] = mapped_column(Text)
    achievements: Mapped[list | None] = mapped_column(JSONB)  # list of strings

    candidate: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="work_experiences")


class Education(Base):
    __tablename__ = "educations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)

    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    degree: Mapped[str | None] = mapped_column(String(200))
    field_of_study: Mapped[str | None] = mapped_column(String(200))
    grade: Mapped[str | None] = mapped_column(String(50))
    start_year: Mapped[int | None] = mapped_column(Integer)
    end_year: Mapped[int | None] = mapped_column(Integer)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(Text)

    candidate: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="educations")


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuing_org: Mapped[str | None] = mapped_column(String(200))
    issue_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    credential_id: Mapped[str | None] = mapped_column(String(200))
    credential_url: Mapped[str | None] = mapped_column(String(500))

    candidate: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="certifications")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    tech_stack: Mapped[list | None] = mapped_column(JSONB)  # list of strings
    project_url: Mapped[str | None] = mapped_column(String(500))
    repo_url: Mapped[str | None] = mapped_column(String(500))
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    candidate: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="projects")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id", ondelete="CASCADE"), nullable=False)

    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    proficiency: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    years_exp: Mapped[float | None] = mapped_column(Float)

    candidate: Mapped["CandidateProfile"] = relationship("CandidateProfile", back_populates="skills")
