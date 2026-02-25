"""Pydantic schemas for applications and job alerts."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.application import ApplicationStatus


class ApplicationAnswerCreate(BaseModel):
    question_id: uuid.UUID
    answer_text: str | None = None


class ApplicationAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    question_id: uuid.UUID
    answer_text: str | None


class ApplyRequest(BaseModel):
    cover_letter: str | None = None
    answers: list[ApplicationAnswerCreate] = []


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    candidate_id: uuid.UUID
    status: ApplicationStatus
    cover_letter: str | None
    resume_url: str | None
    timeline: list | None
    applied_at: datetime
    updated_at: datetime
    answers: list[ApplicationAnswerResponse] = []


class ApplicationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime
    # job details (joined)
    job_title: str | None = None
    company_name: str | None = None
    job_location: str | None = None


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    note: str | None = None


class JobAlertCreate(BaseModel):
    title: str
    keywords: str | None = None
    location: str | None = None
    job_type: str | None = None
    salary_min: int | None = None


class JobAlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    keywords: str | None
    location: str | None
    job_type: str | None
    salary_min: int | None
    is_active: bool
    last_sent_at: datetime | None
    created_at: datetime


# Salary benchmark (static data for now)
class SalaryBenchmark(BaseModel):
    role: str
    location: str
    min_salary: int
    median_salary: int
    max_salary: int
    currency: str = "INR"
    source: str = "DoneHR Benchmark 2025"
