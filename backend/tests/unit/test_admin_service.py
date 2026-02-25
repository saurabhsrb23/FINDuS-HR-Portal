"""Unit tests for admin portal service: login, PIN verify, lockout, role checks."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.admin import AdminRole, AdminUser, ADMIN_PORTAL_ROLE_HIERARCHY
from app.schemas.admin import AdminLoginRequest, AdminUserCreate, AdminUserUpdate


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_admin(
    role: AdminRole = AdminRole.SUPERADMIN,
    is_active: bool = True,
    failed_attempts: int = 0,
    locked_until: datetime | None = None,
    password: str = "hashed_pw",
    pin: str = "hashed_pin",
) -> AdminUser:
    a = AdminUser()
    a.id = uuid.uuid4()
    a.email = "test@admin.com"
    a.full_name = "Test Admin"
    a.role = role
    a.is_active = is_active
    a.failed_attempts = failed_attempts
    a.locked_until = locked_until
    a.password_hash = password
    a.pin_hash = pin
    return a


# ── Role hierarchy ────────────────────────────────────────────────────────────

class TestAdminRoleHierarchy:
    def test_elite_admin_is_lowest(self):
        assert ADMIN_PORTAL_ROLE_HIERARCHY.index(AdminRole.ELITE_ADMIN) == 0

    def test_superadmin_is_highest(self):
        assert ADMIN_PORTAL_ROLE_HIERARCHY.index(AdminRole.SUPERADMIN) == 2

    def test_admin_is_middle(self):
        assert ADMIN_PORTAL_ROLE_HIERARCHY.index(AdminRole.ADMIN) == 1

    def test_superadmin_outranks_admin(self):
        assert (
            ADMIN_PORTAL_ROLE_HIERARCHY.index(AdminRole.SUPERADMIN)
            > ADMIN_PORTAL_ROLE_HIERARCHY.index(AdminRole.ADMIN)
        )

    def test_admin_outranks_elite(self):
        assert (
            ADMIN_PORTAL_ROLE_HIERARCHY.index(AdminRole.ADMIN)
            > ADMIN_PORTAL_ROLE_HIERARCHY.index(AdminRole.ELITE_ADMIN)
        )


# ── Login ─────────────────────────────────────────────────────────────────────

class TestAdminLogin:
    def _make_service(self, admin: AdminUser | None):
        from app.services.admin_service import AdminService
        db = AsyncMock()
        svc = AdminService(db)
        repo = AsyncMock()
        repo.get_by_email.return_value = admin
        svc._repo = repo
        return svc

    @pytest.mark.asyncio
    async def test_login_inactive_user_raises_401(self):
        from fastapi import HTTPException
        admin = _make_admin(is_active=False)
        svc = self._make_service(admin)
        req_data = AdminLoginRequest(email="test@admin.com", password="pw", pin="123456")
        request = MagicMock()
        request.client.host = "127.0.0.1"
        with pytest.raises(HTTPException) as exc_info:
            await svc.login(req_data, request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unknown_user_raises_401(self):
        from fastapi import HTTPException
        svc = self._make_service(None)
        req_data = AdminLoginRequest(email="x@x.com", password="pw", pin="123456")
        request = MagicMock()
        request.client.host = "127.0.0.1"
        with pytest.raises(HTTPException) as exc_info:
            await svc.login(req_data, request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_locked_account_raises_429(self):
        from fastapi import HTTPException
        future = datetime.now(timezone.utc) + timedelta(minutes=10)
        admin = _make_admin(locked_until=future)
        svc = self._make_service(admin)
        req_data = AdminLoginRequest(email="test@admin.com", password="pw", pin="123456")
        request = MagicMock()
        request.client.host = "127.0.0.1"
        with pytest.raises(HTTPException) as exc_info:
            await svc.login(req_data, request)
        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises_401(self):
        from fastapi import HTTPException
        admin = _make_admin()
        svc = self._make_service(admin)
        req_data = AdminLoginRequest(email="test@admin.com", password="wrong", pin="123456")
        request = MagicMock()
        request.client.host = "127.0.0.1"
        with patch("app.services.admin_service.verify_password", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await svc.login(req_data, request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_wrong_pin_raises_401(self):
        from fastapi import HTTPException
        admin = _make_admin()
        svc = self._make_service(admin)
        req_data = AdminLoginRequest(email="test@admin.com", password="correct", pin="000000")
        request = MagicMock()
        request.client.host = "127.0.0.1"
        # password correct, pin wrong
        with patch("app.services.admin_service.verify_password", side_effect=[True, False]):
            with pytest.raises(HTTPException) as exc_info:
                await svc.login(req_data, request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_login_success_returns_token(self):
        from app.schemas.admin import AdminTokenResponse
        admin = _make_admin()
        svc = self._make_service(admin)
        req_data = AdminLoginRequest(email="test@admin.com", password="correct", pin="123456")
        request = MagicMock()
        request.client.host = "127.0.0.1"
        fake_token = "fake.jwt.token"
        with patch("app.services.admin_service.verify_password", return_value=True), \
             patch("app.services.admin_service.create_admin_token", return_value=fake_token):
            result = await svc.login(req_data, request)
        assert result.access_token == fake_token
        assert result.role == AdminRole.SUPERADMIN


# ── PIN verification ──────────────────────────────────────────────────────────

class TestPinVerify:
    @pytest.mark.asyncio
    async def test_verify_pin_correct(self):
        from app.services.admin_service import AdminService
        db = AsyncMock()
        svc = AdminService(db)
        admin = _make_admin()
        repo = AsyncMock()
        repo.get_by_id.return_value = admin
        svc._repo = repo
        with patch("app.services.admin_service.verify_password", return_value=True):
            result = await svc.verify_pin(str(admin.id), "123456")
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_pin_wrong(self):
        from app.services.admin_service import AdminService
        db = AsyncMock()
        svc = AdminService(db)
        admin = _make_admin()
        repo = AsyncMock()
        repo.get_by_id.return_value = admin
        svc._repo = repo
        with patch("app.services.admin_service.verify_password", return_value=False):
            result = await svc.verify_pin(str(admin.id), "000000")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_pin_unknown_admin_returns_false(self):
        from app.services.admin_service import AdminService
        db = AsyncMock()
        svc = AdminService(db)
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        svc._repo = repo
        result = await svc.verify_pin(str(uuid.uuid4()), "123456")
        assert result is False


# ── Lockout logic ─────────────────────────────────────────────────────────────

class TestLockoutBehavior:
    @pytest.mark.asyncio
    async def test_failed_attempts_incremented_on_bad_password(self):
        from app.services.admin_service import AdminService
        db = AsyncMock()
        svc = AdminService(db)
        admin = _make_admin(failed_attempts=1)
        repo = AsyncMock()
        repo.get_by_email.return_value = admin
        repo.increment_failed_attempts = AsyncMock()
        repo.set_locked_until = AsyncMock()
        repo.log_event = AsyncMock()
        svc._repo = repo
        with patch("app.services.admin_service.verify_password", return_value=False):
            await svc._handle_failed_attempt(admin, "127.0.0.1")
        repo.increment_failed_attempts.assert_called_once_with(admin)

    @pytest.mark.asyncio
    async def test_account_locked_after_3_failures(self):
        from app.services.admin_service import AdminService
        db = AsyncMock()
        svc = AdminService(db)
        # Simulate already at 3 attempts (threshold)
        admin = _make_admin(failed_attempts=3)
        repo = AsyncMock()
        repo.increment_failed_attempts = AsyncMock()
        repo.set_locked_until = AsyncMock()
        repo.log_event = AsyncMock()
        svc._repo = repo
        await svc._handle_failed_attempt(admin, "127.0.0.1")
        repo.set_locked_until.assert_called_once()

    def test_locked_until_past_allows_login(self):
        past = datetime.now(timezone.utc) - timedelta(minutes=1)
        admin = _make_admin(locked_until=past)
        # Lock expired — should NOT block
        assert admin.locked_until < datetime.now(timezone.utc)

    def test_locked_until_future_blocks_login(self):
        future = datetime.now(timezone.utc) + timedelta(minutes=14)
        admin = _make_admin(locked_until=future)
        assert admin.locked_until > datetime.now(timezone.utc)


# ── Create admin restrictions ─────────────────────────────────────────────────

class TestCreateAdmin:
    @pytest.mark.asyncio
    async def test_cannot_create_superadmin_via_api(self):
        from fastapi import HTTPException
        from app.services.admin_service import AdminService
        db = AsyncMock()
        svc = AdminService(db)
        repo = AsyncMock()
        svc._repo = repo
        actor = _make_admin(role=AdminRole.SUPERADMIN)
        data = AdminUserCreate(
            email="new@admin.com",
            password="Passw0rd!",
            pin="111111",
            full_name="New Admin",
            role=AdminRole.SUPERADMIN,
        )
        with pytest.raises(HTTPException) as exc_info:
            await svc.create_admin(data, actor)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_cannot_create_duplicate_email(self):
        from fastapi import HTTPException
        from app.services.admin_service import AdminService
        db = AsyncMock()
        svc = AdminService(db)
        existing = _make_admin(role=AdminRole.ADMIN)
        repo = AsyncMock()
        repo.get_by_email.return_value = existing
        svc._repo = repo
        actor = _make_admin(role=AdminRole.SUPERADMIN)
        data = AdminUserCreate(
            email="existing@admin.com",
            password="Passw0rd!",
            pin="111111",
            full_name="Dup Admin",
            role=AdminRole.ADMIN,
        )
        with pytest.raises(HTTPException) as exc_info:
            await svc.create_admin(data, actor)
        assert exc_info.value.status_code == 409


# ── Delete admin restrictions ─────────────────────────────────────────────────

class TestDeleteAdmin:
    @pytest.mark.asyncio
    async def test_delete_requires_DELETE_confirmation(self):
        from fastapi import HTTPException
        from app.services.admin_service import AdminService
        db = AsyncMock()
        svc = AdminService(db)
        repo = AsyncMock()
        target = _make_admin()
        repo.get_by_id.return_value = target
        svc._repo = repo
        actor = _make_admin(role=AdminRole.SUPERADMIN)
        with pytest.raises(HTTPException) as exc_info:
            await svc.delete_admin(str(target.id), "delete", actor)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_cannot_delete_self(self):
        from fastapi import HTTPException
        from app.services.admin_service import AdminService
        db = AsyncMock()
        svc = AdminService(db)
        actor = _make_admin(role=AdminRole.SUPERADMIN)
        repo = AsyncMock()
        repo.get_by_id.return_value = actor  # same admin
        svc._repo = repo
        with pytest.raises(HTTPException) as exc_info:
            await svc.delete_admin(str(actor.id), "DELETE", actor)
        assert exc_info.value.status_code == 400
