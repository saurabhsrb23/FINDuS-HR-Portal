"""AuditLog model — immutable record of every important action."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
    )

    # Actor — nullable for system-generated events
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # What happened
    action: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    # e.g. "user.register", "user.login", "job.create"

    # Target entity
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # Snapshot diff stored as JSONB for flexible querying
    old_value_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(astext_type=sa.Text()), nullable=True
    )
    new_value_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(astext_type=sa.Text()), nullable=True
    )

    # Network context
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} action={self.action} "
            f"user_id={self.user_id}>"
        )
