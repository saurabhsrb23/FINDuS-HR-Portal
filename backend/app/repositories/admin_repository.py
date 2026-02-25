"""Database access layer for admin portal models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin import AdminRole, AdminSession, AdminUser, PlatformEvent
from app.schemas.admin import AdminUserCreate, AdminUserUpdate


class AdminRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── AdminUser ─────────────────────────────────────────────────────────────

    async def get_by_email(self, email: str) -> AdminUser | None:
        result = await self._db.execute(
            select(AdminUser).where(AdminUser.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, admin_id: uuid.UUID | str) -> AdminUser | None:
        if isinstance(admin_id, str):
            admin_id = uuid.UUID(admin_id)
        result = await self._db.execute(
            select(AdminUser).where(AdminUser.id == admin_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: AdminUserCreate, password_hash: str, pin_hash: str) -> AdminUser:
        admin = AdminUser(
            email=data.email.lower(),
            password_hash=password_hash,
            pin_hash=pin_hash,
            full_name=data.full_name,
            role=data.role,
        )
        self._db.add(admin)
        await self._db.flush()
        return admin

    async def update(self, admin: AdminUser, data: AdminUserUpdate, new_pin_hash: str | None = None) -> AdminUser:
        if data.full_name is not None:
            admin.full_name = data.full_name
        if data.role is not None:
            admin.role = data.role
        if data.is_active is not None:
            admin.is_active = data.is_active
        if new_pin_hash is not None:
            admin.pin_hash = new_pin_hash
        self._db.add(admin)
        await self._db.flush()
        return admin

    async def delete(self, admin: AdminUser) -> None:
        await self._db.delete(admin)
        await self._db.flush()

    async def list_all(self) -> list[AdminUser]:
        result = await self._db.execute(
            select(AdminUser).order_by(AdminUser.created_at.desc())
        )
        return list(result.scalars().all())

    async def increment_failed_attempts(self, admin: AdminUser) -> None:
        admin.failed_attempts = (admin.failed_attempts or 0) + 1
        self._db.add(admin)
        await self._db.flush()

    async def reset_failed_attempts(self, admin: AdminUser) -> None:
        admin.failed_attempts = 0
        admin.locked_until = None
        self._db.add(admin)
        await self._db.flush()

    async def set_locked_until(self, admin: AdminUser, until: datetime) -> None:
        admin.locked_until = until
        self._db.add(admin)
        await self._db.flush()

    async def set_last_login(self, admin: AdminUser) -> None:
        admin.last_login_at = datetime.now(timezone.utc)
        self._db.add(admin)
        await self._db.flush()

    # ── PlatformEvent ─────────────────────────────────────────────────────────

    async def log_event(
        self,
        event_type: str,
        actor_id: uuid.UUID | None = None,
        actor_role: str | None = None,
        target_id: str | None = None,
        target_type: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> PlatformEvent:
        event = PlatformEvent(
            event_type=event_type,
            actor_id=actor_id,
            actor_role=actor_role,
            target_id=target_id,
            target_type=target_type,
            details=details,
            ip_address=ip_address,
        )
        self._db.add(event)
        await self._db.flush()
        return event

    async def list_events(
        self,
        event_type: str | None = None,
        actor_role: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[PlatformEvent], int]:
        query = select(PlatformEvent)
        if event_type:
            query = query.where(PlatformEvent.event_type == event_type)
        if actor_role:
            query = query.where(PlatformEvent.actor_role == actor_role)
        count_result = await self._db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()
        query = query.order_by(PlatformEvent.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self._db.execute(query)
        return list(result.scalars().all()), total

    async def count_events_today(self, event_type: str | None = None) -> int:
        from datetime import date
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
        query = select(func.count(PlatformEvent.id)).where(PlatformEvent.created_at >= today_start)
        if event_type:
            query = query.where(PlatformEvent.event_type == event_type)
        result = await self._db.execute(query)
        return result.scalar_one()
