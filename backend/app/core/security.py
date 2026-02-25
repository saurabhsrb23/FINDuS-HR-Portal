"""JWT creation / verification and password hashing utilities."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ─── Password hashing (bcrypt, cost factor 12) ────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    """Return a bcrypt-hashed version of *password*."""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if *plain_password* matches *hashed_password*."""
    return _pwd_context.verify(plain_password, hashed_password)


# ─── Token helpers ────────────────────────────────────────────────────────────
def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _encode(payload: dict[str, Any], secret: str) -> str:
    return jwt.encode(payload, secret, algorithm=settings.ALGORITHM)


def _decode(token: str, secret: str, **kwargs: Any) -> dict[str, Any]:
    return jwt.decode(token, secret, algorithms=[settings.ALGORITHM], **kwargs)


# ─── User JWT ─────────────────────────────────────────────────────────────────
def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a short-lived access token (default: ACCESS_TOKEN_EXPIRE_MINUTES)."""
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = _now_utc() + delta
    to_encode = {
        **data,
        "exp": expire,
        "iat": _now_utc(),
        "type": "access",
    }
    return _encode(to_encode, settings.SECRET_KEY.get_secret_value())


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a long-lived refresh token (default: REFRESH_TOKEN_EXPIRE_DAYS)."""
    expire = _now_utc() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        **data,
        "exp": expire,
        "iat": _now_utc(),
        "type": "refresh",
    }
    return _encode(to_encode, settings.SECRET_KEY.get_secret_value())


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a user JWT. Raises HTTP 401 on any failure."""
    try:
        payload = _decode(token, settings.SECRET_KEY.get_secret_value())
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ─── Admin JWT ────────────────────────────────────────────────────────────────
def create_admin_token(data: dict[str, Any]) -> str:
    """Create an admin-scoped JWT signed with ADMIN_JWT_SECRET, aud='admin_portal'."""
    expire = _now_utc() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        **data,
        "exp": expire,
        "iat": _now_utc(),
        "type": "access",
        "aud": "admin_portal",
    }
    return _encode(to_encode, settings.ADMIN_JWT_SECRET.get_secret_value())


def decode_admin_token(token: str) -> dict[str, Any]:
    """Decode an admin JWT. Validates audience='admin_portal'. Raises 401 on failure."""
    try:
        payload = _decode(
            token,
            settings.ADMIN_JWT_SECRET.get_secret_value(),
            audience="admin_portal",
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ─── Email / password-reset token helpers ────────────────────────────────────
def create_email_verification_token(user_id: str) -> str:
    """One-time 24-hour token for email verification."""
    expire = _now_utc() + timedelta(hours=24)
    return _encode(
        {"sub": user_id, "type": "email_verification", "exp": expire},
        settings.SECRET_KEY.get_secret_value(),
    )


def create_password_reset_token(user_id: str) -> str:
    """One-time 1-hour token for password reset."""
    expire = _now_utc() + timedelta(hours=1)
    return _encode(
        {"sub": user_id, "type": "password_reset", "exp": expire},
        settings.SECRET_KEY.get_secret_value(),
    )


def decode_typed_token(token: str, expected_type: str) -> dict[str, Any]:
    """Decode a token and verify it matches the expected type claim."""
    payload = decode_token(token)
    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid token type. Expected '{expected_type}'.",
        )
    return payload
