"""Pydantic schemas for candidate profiles."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.candidate import EmploymentType


class WorkExperienceCreate(BaseModel):
    company_name: str
    job_title: str
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    location: str | None = None
    is_current: bool = False
    start_date: datetime | None = None
    end_date: datetime | None = None
    description: str | None = None
    achievements: list[str] | None = None


class WorkExperienceResponse(WorkExperienceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class EducationCreate(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    grade: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    is_current: bool = False
    description: str | None = None


class EducationResponse(EducationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class CertificationCreate(BaseModel):
    name: str
    issuing_org: str | None = None
    issue_date: datetime | None = None
    expiry_date: datetime | None = None
    credential_id: str | None = None
    credential_url: str | None = None


class CertificationResponse(CertificationCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    tech_stack: list[str] | None = None
    project_url: str | None = None
    repo_url: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class ProjectResponse(ProjectCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class CandidateSkillCreate(BaseModel):
    skill_name: str
    proficiency: int = Field(default=3, ge=1, le=5)
    years_exp: float | None = None


class CandidateSkillResponse(CandidateSkillCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class CandidateProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    location: str | None = None
    headline: str | None = None
    summary: str | None = None
    desired_role: str | None = None
    desired_salary_min: int | None = None
    desired_salary_max: int | None = None
    desired_location: str | None = None
    open_to_remote: bool | None = None
    notice_period_days: int | None = None
    years_of_experience: float | None = None


class CandidateProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str | None
    phone: str | None
    location: str | None
    headline: str | None
    summary: str | None
    avatar_url: str | None
    resume_url: str | None
    resume_filename: str | None
    desired_role: str | None
    desired_salary_min: int | None
    desired_salary_max: int | None
    desired_location: str | None
    open_to_remote: bool
    notice_period_days: int | None
    years_of_experience: float | None
    profile_strength: int
    created_at: datetime
    updated_at: datetime
    work_experiences: list[WorkExperienceResponse] = []
    educations: list[EducationResponse] = []
    certifications: list[CertificationResponse] = []
    projects: list[ProjectResponse] = []
    skills: list[CandidateSkillResponse] = []


class ProfileStrengthResponse(BaseModel):
    score: int
    breakdown: dict[str, int]
    tips: list[str]
