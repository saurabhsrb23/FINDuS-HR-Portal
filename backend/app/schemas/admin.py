"""Pydantic schemas for the admin portal."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.models.admin import AdminRole


# ── Auth ──────────────────────────────────────────────────────────────────────

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str
    pin: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_id: str
    role: AdminRole
    full_name: str


class AdminPinVerifyRequest(BaseModel):
    pin: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


# ── Admin user management ─────────────────────────────────────────────────────

class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    pin: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    full_name: str = Field(..., min_length=2, max_length=255)
    role: AdminRole = AdminRole.ADMIN


class AdminUserUpdate(BaseModel):
    full_name: str | None = None
    role: AdminRole | None = None
    is_active: bool | None = None
    pin: str | None = Field(default=None, min_length=6, max_length=6, pattern=r"^\d{6}$")


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: AdminRole
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Platform stats ────────────────────────────────────────────────────────────

class PlatformOverview(BaseModel):
    total_users: int
    total_candidates: int
    total_hr_users: int
    total_jobs: int
    active_jobs: int
    total_applications: int
    total_companies: int
    active_ws_connections: int
    platform_events_today: int


class MonitoringMetrics(BaseModel):
    active_ws_connections: int
    db_latency_ms: float
    redis_connected_clients: int
    redis_used_memory_mb: float
    redis_hit_rate: float
    groq_calls_today: int
    error_events_today: int
    uptime_seconds: float


# ── User listings ─────────────────────────────────────────────────────────────

class UserListItem(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserListItem]
    total: int
    page: int
    page_size: int


# ── Company management ────────────────────────────────────────────────────────

class CompanyListItem(BaseModel):
    id: uuid.UUID
    name: str
    website: str | None
    industry: str | None
    is_verified: bool
    is_active: bool
    hr_email: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyStatusUpdate(BaseModel):
    is_verified: bool | None = None
    is_active: bool | None = None


# ── Platform events ───────────────────────────────────────────────────────────

class PlatformEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    actor_id: uuid.UUID | None
    actor_role: str | None
    target_id: str | None
    target_type: str | None
    details: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PlatformEventListResponse(BaseModel):
    items: list[PlatformEventResponse]
    total: int
    page: int
    page_size: int


# ── Announcements ─────────────────────────────────────────────────────────────

class AnnouncementRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    target_role: str | None = None  # None = broadcast to all
