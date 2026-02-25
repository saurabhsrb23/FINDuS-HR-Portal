"""User SQLAlchemy model with role enum and soft-delete support."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(str, Enum):
    CANDIDATE = "candidate"
    HR = "hr"
    HR_ADMIN = "hr_admin"
    HIRING_MANAGER = "hiring_manager"
    RECRUITER = "recruiter"
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    ELITE_ADMIN = "elite_admin"


# Ordered list used for hierarchy comparisons (index = privilege level)
ADMIN_ROLE_HIERARCHY: list[UserRole] = [
    UserRole.ADMIN,
    UserRole.SUPERADMIN,
    UserRole.ELITE_ADMIN,
]


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role_enum", create_type=False,
               values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=UserRole.CANDIDATE,
        server_default=UserRole.CANDIDATE.value,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=sa.text("true")
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=sa.text("false")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"

    @property
    def is_admin_user(self) -> bool:
        return self.role in ADMIN_ROLE_HIERARCHY

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
