"""Admin portal business logic."""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_admin_token,
    hash_password,
    verify_password,
)
from app.models.admin import AdminRole, AdminUser, ADMIN_PORTAL_ROLE_HIERARCHY
from app.models.application import Application
from app.models.candidate import CandidateProfile
from app.models.company import Company
from app.models.job import Job, JobStatus
from app.models.user import User, UserRole
from app.repositories.admin_repository import AdminRepository
from app.schemas.admin import (
    AdminLoginRequest,
    AdminTokenResponse,
    AdminUserCreate,
    AdminUserUpdate,
    AnnouncementRequest,
    CompanyListItem,
    CompanyStatusUpdate,
    MonitoringMetrics,
    PlatformOverview,
    UserListItem,
    UserListResponse,
)

log = structlog.get_logger("donehr.admin_service")

_MAX_FAILED_ATTEMPTS = 3
_LOCKOUT_MINUTES = 15


class AdminService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = AdminRepository(db)

    # -- Auth --

    async def login(self, data: AdminLoginRequest, request: Request) -> AdminTokenResponse:
        ip = request.client.host if request.client else None
        admin = await self._repo.get_by_email(data.email)
        if not admin or not admin.is_active:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        # Check lockout
        if admin.locked_until and admin.locked_until > datetime.now(timezone.utc):
            remaining = int((admin.locked_until - datetime.now(timezone.utc)).total_seconds() / 60) + 1
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account locked. Try again in {remaining} minute(s).",
            )

        # Verify password
        if not verify_password(data.password, admin.password_hash):
            await self._handle_failed_attempt(admin, ip)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        # Verify PIN
        if not verify_password(data.pin, admin.pin_hash):
            await self._handle_failed_attempt(admin, ip)
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN")

        # Success -- reset counters
        await self._repo.reset_failed_attempts(admin)
        await self._repo.set_last_login(admin)

        token = create_admin_token({"sub": str(admin.id), "role": admin.role.value})

        await self._repo.log_event(
            "admin_login",
            actor_id=admin.id,
            actor_role=admin.role.value,
            details={"email": admin.email},
            ip_address=ip,
        )
        await self._db.commit()

        return AdminTokenResponse(
            access_token=token,
            admin_id=str(admin.id),
            role=admin.role,
            full_name=admin.full_name,
        )

    async def _handle_failed_attempt(self, admin: AdminUser, ip: str | None) -> None:
        await self._repo.increment_failed_attempts(admin)
        if admin.failed_attempts >= _MAX_FAILED_ATTEMPTS:
            lock_until = datetime.now(timezone.utc) + timedelta(minutes=_LOCKOUT_MINUTES)
            await self._repo.set_locked_until(admin, lock_until)
            await self._repo.log_event(
                "admin_account_locked",
                actor_id=admin.id,
                actor_role=admin.role.value,
                details={"email": admin.email, "attempts": admin.failed_attempts},
                ip_address=ip,
            )
            try:
                from app.tasks.email_tasks import send_verification_email
                log.warning("admin_locked_email_alert", email=admin.email, locked_until=str(lock_until))
            except Exception:
                pass
        await self._db.commit()

    async def verify_pin(self, admin_id: str, pin: str) -> bool:
        admin = await self._repo.get_by_id(admin_id)
        if not admin:
            return False
        return verify_password(pin, admin.pin_hash)

    # -- Platform overview --

    async def get_platform_overview(self) -> PlatformOverview:
        from app.core.websocket_manager import ws_manager

        async def _count(model, *conditions):
            q = select(func.count(model.id))
            for c in conditions:
                q = q.where(c)
            r = await self._db.execute(q)
            return r.scalar_one()

        total_users = await _count(User)
        total_candidates = await _count(User, User.role == UserRole.CANDIDATE)
        total_hr = await _count(User, User.role.in_([
            UserRole.HR, UserRole.HR_ADMIN, UserRole.HIRING_MANAGER, UserRole.RECRUITER
        ]))
        total_jobs = await _count(Job)
        active_jobs = await _count(Job, Job.status == JobStatus.ACTIVE)
        total_apps = await _count(Application)
        total_companies = await _count(Company)
        events_today = await self._repo.count_events_today()

        return PlatformOverview(
            total_users=total_users,
            total_candidates=total_candidates,
            total_hr_users=total_hr,
            total_jobs=total_jobs,
            active_jobs=active_jobs,
            total_applications=total_apps,
            total_companies=total_companies,
            active_ws_connections=len(ws_manager.active_connections),
            platform_events_today=events_today,
        )

    # -- Monitoring metrics --

    async def get_monitoring_metrics(self) -> MonitoringMetrics:
        from app.core.websocket_manager import ws_manager
        from app.core.redis_client import get_redis

        t0 = time.monotonic()
        await self._db.execute(select(func.now()))
        db_latency = (time.monotonic() - t0) * 1000

        redis_clients = 0
        redis_memory_mb = 0.0
        redis_hit_rate = 0.0
        try:
            redis = get_redis()
            info = await redis.info()
            redis_clients = int(info.get("connected_clients", 0))
            redis_memory_mb = round(int(info.get("used_memory", 0)) / 1024 / 1024, 2)
            hits = int(info.get("keyspace_hits", 1))
            misses = int(info.get("keyspace_misses", 0))
            redis_hit_rate = round(hits / max(hits + misses, 1) * 100, 1)
        except Exception:
            pass

        groq_calls = await self._repo.count_events_today("groq_api_call")
        error_events = await self._repo.count_events_today("error")

        import time as _time
        uptime = _time.monotonic()

        return MonitoringMetrics(
            active_ws_connections=len(ws_manager.active_connections),
            db_latency_ms=round(db_latency, 2),
            redis_connected_clients=redis_clients,
            redis_used_memory_mb=redis_memory_mb,
            redis_hit_rate=redis_hit_rate,
            groq_calls_today=groq_calls,
            error_events_today=error_events,
            uptime_seconds=round(uptime, 1),
        )

    # -- User management --

    async def list_users(
        self,
        role_filter: str | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> UserListResponse:
        query = select(User)
        if role_filter:
            try:
                query = query.where(User.role == UserRole(role_filter))
            except ValueError:
                pass
        if search:
            pattern = f"%{search}%"
            query = query.where(
                User.email.ilike(pattern) | User.full_name.ilike(pattern)
            )
        count_result = await self._db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()
        result = await self._db.execute(
            query.order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        users = list(result.scalars().all())
        return UserListResponse(
            items=[UserListItem.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def deactivate_user(self, user_id: str, actor: AdminUser) -> None:
        from app.repositories.user_repository import UserRepository
        repo = UserRepository(self._db)
        user = await repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        user.is_active = False
        self._db.add(user)
        await self._repo.log_event(
            "user_deactivated",
            actor_id=actor.id,
            actor_role=actor.role.value,
            target_id=str(user.id),
            target_type="user",
            details={"email": user.email},
        )
        await self._db.commit()

    # -- Company management --

    async def list_companies(self, page: int = 1, page_size: int = 20) -> tuple[list[CompanyListItem], int]:
        query = select(Company)
        count_result = await self._db.execute(select(func.count()).select_from(query.subquery()))
        total = count_result.scalar_one()
        result = await self._db.execute(
            query.order_by(Company.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
        companies = list(result.scalars().all())
        items = []
        for c in companies:
            hr_result = await self._db.execute(select(User).where(User.id == c.hr_id))
            hr = hr_result.scalar_one_or_none()
            items.append(CompanyListItem(
                id=c.id,
                name=c.name,
                website=getattr(c, "website", None),
                industry=getattr(c, "industry", None),
                is_verified=getattr(c, "is_verified", False),
                is_active=getattr(c, "is_active", True),
                hr_email=hr.email if hr else None,
                created_at=c.created_at,
            ))
        return items, total

    async def update_company_status(self, company_id: str, data: CompanyStatusUpdate, actor: AdminUser) -> None:
        result = await self._db.execute(select(Company).where(Company.id == uuid.UUID(company_id)))
        company = result.scalar_one_or_none()
        if not company:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Company not found")
        if data.is_verified is not None:
            company.is_verified = data.is_verified  # type: ignore[assignment]
        if data.is_active is not None:
            company.is_active = data.is_active  # type: ignore[assignment]
        self._db.add(company)
        await self._repo.log_event(
            "company_status_updated",
            actor_id=actor.id,
            actor_role=actor.role.value,
            target_id=company_id,
            target_type="company",
            details=data.model_dump(exclude_none=True),
        )
        await self._db.commit()

    # -- Admin user management --

    async def list_admins(self) -> list[AdminUser]:
        return await self._repo.list_all()

    async def create_admin(self, data: AdminUserCreate, actor: AdminUser) -> AdminUser:
        if data.role == AdminRole.SUPERADMIN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Cannot create superadmin via API")
        existing = await self._repo.get_by_email(data.email)
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered")
        admin = await self._repo.create(
            data,
            password_hash=hash_password(data.password),
            pin_hash=hash_password(data.pin),
        )
        await self._repo.log_event(
            "admin_created",
            actor_id=actor.id,
            actor_role=actor.role.value,
            target_id=str(admin.id),
            target_type="admin_user",
            details={"email": admin.email, "role": admin.role.value},
        )
        await self._db.commit()
        await self._db.refresh(admin)
        return admin

    async def update_admin(self, admin_id: str, data: AdminUserUpdate, actor: AdminUser) -> AdminUser:
        admin = await self._repo.get_by_id(admin_id)
        if not admin:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Admin not found")
        new_pin_hash = hash_password(data.pin) if data.pin else None
        admin = await self._repo.update(admin, data, new_pin_hash=new_pin_hash)
        await self._repo.log_event(
            "admin_updated",
            actor_id=actor.id,
            actor_role=actor.role.value,
            target_id=admin_id,
            target_type="admin_user",
            details=data.model_dump(exclude_none=True, exclude={"pin"}),
        )
        await self._db.commit()
        await self._db.refresh(admin)
        return admin

    async def delete_admin(self, admin_id: str, confirmation: str, actor: AdminUser) -> None:
        if confirmation != "DELETE":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Must type DELETE to confirm")
        admin = await self._repo.get_by_id(admin_id)
        if not admin:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Admin not found")
        if str(admin.id) == str(actor.id):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")
        await self._repo.log_event(
            "admin_deleted",
            actor_id=actor.id,
            actor_role=actor.role.value,
            target_id=admin_id,
            target_type="admin_user",
            details={"email": admin.email},
        )
        await self._repo.delete(admin)
        await self._db.commit()

    # -- Announcements --

    async def send_announcement(self, data: AnnouncementRequest, actor: AdminUser) -> None:
        from app.core.event_emitter import emit_event
        payload = {"message": data.message, "from": actor.full_name, "role": actor.role.value}
        await emit_event(
            "announcement",
            payload,
            target_role=data.target_role,
        )
        await self._repo.log_event(
            "announcement_sent",
            actor_id=actor.id,
            actor_role=actor.role.value,
            details={"message": data.message, "target_role": data.target_role},
        )
        await self._db.commit()
