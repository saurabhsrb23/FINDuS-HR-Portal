"""Pydantic v2 schemas for all authentication endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.models.user import UserRole


# ─── Shared config ────────────────────────────────────────────────────────────
class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ─── Registration ─────────────────────────────────────────────────────────────
class RegisterRequest(_Base):
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=128)]
    confirm_password: Annotated[str, Field(min_length=8, max_length=128)]
    full_name: Annotated[str, Field(min_length=1, max_length=255)]
    role: UserRole = UserRole.CANDIDATE
    company_name: Annotated[str | None, Field(default=None, max_length=255)]

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        errors: list[str] = []
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in v):
            errors.append("at least one special character")
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> RegisterRequest:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


# ─── Login ────────────────────────────────────────────────────────────────────
class LoginRequest(_Base):
    email: EmailStr
    password: Annotated[str, Field(min_length=1, max_length=128)]


# ─── Token responses ──────────────────────────────────────────────────────────
class TokenResponse(_Base):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: uuid.UUID


class RefreshRequest(_Base):
    refresh_token: str


class AccessTokenResponse(_Base):
    access_token: str
    token_type: str = "bearer"


# ─── User response ────────────────────────────────────────────────────────────
class UserResponse(_Base):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_verified: bool
    is_active: bool
    created_at: datetime


# ─── Password reset ───────────────────────────────────────────────────────────
class ForgotPasswordRequest(_Base):
    email: EmailStr


class ResetPasswordRequest(_Base):
    token: str
    new_password: Annotated[str, Field(min_length=8, max_length=128)]
    confirm_password: Annotated[str, Field(min_length=8, max_length=128)]

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        errors: list[str] = []
        if not any(c.isupper() for c in v):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in v):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            errors.append("at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in v):
            errors.append("at least one special character")
        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> ResetPasswordRequest:
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


# ─── Generic message ──────────────────────────────────────────────────────────
class MessageResponse(_Base):
    message: str
