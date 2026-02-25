"""UserRepository — all DB operations for the User model."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    """Thin data-access layer for the `users` table."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── Reads ────────────────────────────────────────────────────────────────
    async def get_by_email(self, email: str) -> User | None:
        """Return a non-deleted user by email, or None."""
        result = await self.db.execute(
            select(User)
            .where(User.email == email.lower().strip())
            .where(User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str | uuid.UUID) -> User | None:
        """Return a non-deleted user by primary key, or None."""
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .where(User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    # ─── Writes ───────────────────────────────────────────────────────────────
    async def create_user(
        self,
        *,
        email: str,
        password_hash: str,
        full_name: str,
        role: UserRole = UserRole.CANDIDATE,
    ) -> User:
        """Insert and return a new User row."""
        user = User(
            id=uuid.uuid4(),
            email=email.lower().strip(),
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()   # populate server-side defaults (created_at, etc.)
        await self.db.refresh(user)
        return user

    async def update_user(
        self,
        user_id: str | uuid.UUID,
        **fields: Any,
    ) -> User | None:
        """
        Partial update of a user row. Supported fields:
        full_name, password_hash, is_active, is_verified, role.
        Returns the updated User or None if not found.
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return None

        allowed = {"full_name", "password_hash", "is_active", "is_verified", "role"}
        for key, value in fields.items():
            if key in allowed:
                setattr(user, key, value)

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def soft_delete_user(self, user_id: str | uuid.UUID) -> bool:
        """Set deleted_at to now. Returns True if the user existed and was deleted."""
        user = await self.get_by_id(user_id)
        if user is None:
            return False
        user.deleted_at = datetime.now(tz=timezone.utc)
        user.is_active = False
        await self.db.flush()
        return True

    async def email_exists(self, email: str) -> bool:
        """Return True if any user (including soft-deleted) has this email."""
        result = await self.db.execute(
            select(User.id).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none() is not None
