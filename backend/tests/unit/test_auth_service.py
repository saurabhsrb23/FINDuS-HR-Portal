"""Unit tests for AuthService — all external dependencies are mocked."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
)
from app.models.user import User, UserRole
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.services.auth_service import AuthService
from tests.conftest import make_user


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _build_service(*, repo_overrides: dict | None = None) -> tuple[AuthService, MagicMock]:
    """Return (service, mock_repo) with a mocked DB session."""
    mock_db = AsyncMock()
    service = AuthService(mock_db)

    mock_repo = AsyncMock()
    defaults = {
        "email_exists": AsyncMock(return_value=False),
        "create_user": AsyncMock(return_value=make_user()),
        "get_by_email": AsyncMock(return_value=None),
        "get_by_id": AsyncMock(return_value=None),
        "update_user": AsyncMock(return_value=make_user()),
    }
    if repo_overrides:
        defaults.update(repo_overrides)
    for name, value in defaults.items():
        setattr(mock_repo, name, value)

    service.repo = mock_repo
    return service, mock_repo


# ─── register ─────────────────────────────────────────────────────────────────
@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_success():
    service, repo = _build_service()
    data = RegisterRequest(
        email="new@example.com",
        password="Valid@123!",
        confirm_password="Valid@123!",
        full_name="New User",
        role=UserRole.CANDIDATE,
    )
    with patch("app.tasks.email_tasks.send_verification_email") as mock_task:
        mock_task.delay = MagicMock()
        result = await service.register(data)

    assert result.email == make_user().email
    repo.create_user.assert_awaited_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_duplicate_email_raises_409():
    service, repo = _build_service(
        repo_overrides={"email_exists": AsyncMock(return_value=True)}
    )
    data = RegisterRequest(
        email="dup@example.com",
        password="Valid@123!",
        confirm_password="Valid@123!",
        full_name="Dup User",
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.register(data)

    assert exc_info.value.status_code == 409


# ─── login ────────────────────────────────────────────────────────────────────
@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_success():
    real_password = "Valid@123!"
    user = make_user()
    user.password_hash = hash_password(real_password)

    service, repo = _build_service(
        repo_overrides={"get_by_email": AsyncMock(return_value=user)}
    )
    data = LoginRequest(email=user.email, password=real_password)
    result = await service.login(data)

    assert result.access_token
    assert result.refresh_token
    assert result.role == user.role


@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_wrong_password_raises_401():
    real_password = "Valid@123!"
    user = make_user()
    user.password_hash = hash_password(real_password)

    service, _ = _build_service(
        repo_overrides={"get_by_email": AsyncMock(return_value=user)}
    )
    data = LoginRequest(email=user.email, password="WrongPass@1!")
    with pytest.raises(HTTPException) as exc_info:
        await service.login(data)

    assert exc_info.value.status_code == 401


@pytest.mark.unit
@pytest.mark.asyncio
async def test_login_unverified_raises_403():
    real_password = "Valid@123!"
    user = make_user(is_verified=False)
    user.password_hash = hash_password(real_password)

    service, _ = _build_service(
        repo_overrides={"get_by_email": AsyncMock(return_value=user)}
    )
    data = LoginRequest(email=user.email, password=real_password)
    with pytest.raises(HTTPException) as exc_info:
        await service.login(data)

    assert exc_info.value.status_code == 403
    assert "not verified" in exc_info.value.detail.lower()


# ─── refresh_token ────────────────────────────────────────────────────────────
@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_token_valid():
    user = make_user()
    token_data = {"sub": str(user.id), "role": user.role.value}
    valid_refresh = create_refresh_token(token_data)

    service, repo = _build_service(
        repo_overrides={"get_by_id": AsyncMock(return_value=user)}
    )

    with patch("app.services.auth_service.is_token_blacklisted", AsyncMock(return_value=False)), \
         patch("app.services.auth_service.blacklist_token", AsyncMock()):
        result = await service.refresh_token(RefreshRequest(refresh_token=valid_refresh))

    assert result.access_token
    assert result.refresh_token != valid_refresh  # rotated


@pytest.mark.unit
@pytest.mark.asyncio
async def test_refresh_token_expired_raises_401():
    # Create a token that expired 1 hour ago
    from datetime import timedelta
    from app.core.security import create_refresh_token as _crt
    expired_token = _crt.__wrapped__({}) if hasattr(_crt, "__wrapped__") else None

    # Simulate with a manually crafted expired token using jose
    from jose import jwt as jose_jwt
    from app.core.config import settings
    payload = {
        "sub": str(uuid.uuid4()),
        "type": "refresh",
        "exp": datetime.now(tz=timezone.utc) - timedelta(hours=1),
        "iat": datetime.now(tz=timezone.utc) - timedelta(hours=2),
    }
    expired = jose_jwt.encode(
        payload,
        settings.SECRET_KEY.get_secret_value(),
        algorithm=settings.ALGORITHM,
    )

    service, _ = _build_service()
    with pytest.raises(HTTPException) as exc_info:
        await service.refresh_token(RefreshRequest(refresh_token=expired))

    assert exc_info.value.status_code == 401


# ─── logout / blacklist ───────────────────────────────────────────────────────
@pytest.mark.unit
@pytest.mark.asyncio
async def test_logout_blacklists_token():
    user = make_user()
    token = create_access_token({"sub": str(user.id), "role": user.role.value})

    service, _ = _build_service()

    with patch("app.services.auth_service.blacklist_token", new_callable=AsyncMock) as mock_bl:
        result = await service.logout(token)

    assert result.message == "Logged out successfully"
    mock_bl.assert_awaited_once()
    # First arg should be the token itself
    assert mock_bl.call_args[0][0] == token


@pytest.mark.unit
@pytest.mark.asyncio
async def test_logout_invalid_token_is_noop():
    """Logging out with an already-expired / garbage token must NOT raise."""
    service, _ = _build_service()
    result = await service.logout("not.a.valid.token")
    assert "successfully" in result.message
