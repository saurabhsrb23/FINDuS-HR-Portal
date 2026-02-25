"""AuthService — all business logic for authentication."""
from __future__ import annotations

import math
from datetime import datetime, timezone

import structlog
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis_client import blacklist_token, is_token_blacklisted
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_typed_token,
    hash_password,
    verify_password,
)
from app.models.user import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)

log = structlog.get_logger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = UserRepository(db)

    # ─── Register ─────────────────────────────────────────────────────────────
    async def register(
        self,
        data: RegisterRequest,
        ip_address: str | None = None,
    ) -> UserResponse:
        """
        Register a new user account.
        1. Reject duplicate emails (409).
        2. Hash password (bcrypt 12 rounds).
        3. Persist user row.
        4. Dispatch verification email via Celery (fire-and-forget).
        """
        if await self.repo.email_exists(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        password_hash = hash_password(data.password)
        user = await self.repo.create_user(
            email=data.email,
            password_hash=password_hash,
            full_name=data.full_name,
            role=data.role,
        )

        # Fire-and-forget: send verification email
        verification_token = create_email_verification_token(str(user.id))
        verification_url = (
            f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        )

        try:
            from app.tasks.email_tasks import send_verification_email
            send_verification_email.delay(str(user.id), user.email, verification_url)
        except Exception:
            # Non-fatal — email delivery failure should not block registration
            log.warning(
                "verification_email_dispatch_failed",
                user_id=str(user.id),
                email=user.email,
            )

        log.info("user_registered", user_id=str(user.id), role=user.role.value)

        # Real-time event: notify HR users when a new candidate registers
        if user.role.value == "candidate":
            try:
                from app.core.event_emitter import emit_event
                await emit_event(
                    "new_candidate_registered",
                    {"user_id": str(user.id), "name": user.full_name, "email": user.email},
                    target_role="hr_all",
                )
            except Exception:
                pass

        return UserResponse.model_validate(user)

    # ─── Login ────────────────────────────────────────────────────────────────
    async def login(
        self,
        data: LoginRequest,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """
        Authenticate a user.
        - Wrong password → 401
        - Email not verified → 403
        - Account inactive → 403
        """
        user = await self.repo.get_by_email(data.email)

        # Constant-time guard: always call verify_password even if user is None
        _dummy_hash = "$2b$12$KIXRrFQtcKtLJkxDvYtD5eSInlYbTFWk0k1wB1g1rRZnzN9F5xZ3."
        password_ok = verify_password(
            data.password,
            user.password_hash if user else _dummy_hash,
        )

        if user is None or not password_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email address not verified. Please check your inbox.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been deactivated. Contact support.",
            )

        token_data = {"sub": str(user.id), "role": user.role.value}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        log.info("user_login", user_id=str(user.id), ip=ip_address)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            role=user.role,
            user_id=user.id,
        )

    # ─── Refresh ──────────────────────────────────────────────────────────────
    async def refresh_token(self, data: RefreshRequest) -> TokenResponse:
        """
        Issue a new access token from a valid refresh token.
        Also rotates the refresh token (issues a new one).
        """
        try:
            payload = decode_typed_token(data.refresh_token, "refresh")
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid or expired",
            )

        if await is_token_blacklisted(data.refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        user_id: str = payload.get("sub", "")
        user = await self.repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Rotate — blacklist old refresh token
        exp = payload.get("exp", 0)
        remaining = max(0, int(exp - datetime.now(tz=timezone.utc).timestamp()))
        await blacklist_token(data.refresh_token, remaining)

        token_data = {"sub": str(user.id), "role": user.role.value}
        new_access = create_access_token(token_data)
        new_refresh = create_refresh_token(token_data)

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            role=user.role,
            user_id=user.id,
        )

    # ─── Logout ───────────────────────────────────────────────────────────────
    async def logout(self, access_token: str) -> MessageResponse:
        """
        Blacklist the provided access token in Redis so it cannot be reused.
        TTL = remaining token lifetime.
        """
        try:
            payload = jwt.decode(
                access_token,
                settings.SECRET_KEY.get_secret_value(),
                algorithms=[settings.ALGORITHM],
            )
        except JWTError:
            # Token already expired or invalid — logout is a no-op
            return MessageResponse(message="Logged out successfully")

        exp = payload.get("exp", 0)
        remaining = max(1, int(exp - datetime.now(tz=timezone.utc).timestamp()))
        await blacklist_token(access_token, remaining)

        log.info("user_logout", user_id=payload.get("sub"))
        return MessageResponse(message="Logged out successfully")

    # ─── Email verification ───────────────────────────────────────────────────
    async def verify_email(self, token: str) -> MessageResponse:
        """Mark the user's email as verified."""
        payload = decode_typed_token(token, "email_verification")
        user_id: str = payload.get("sub", "")

        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        if user.is_verified:
            return MessageResponse(message="Email is already verified")

        await self.repo.update_user(user_id, is_verified=True)
        log.info("email_verified", user_id=user_id)
        return MessageResponse(message="Email verified successfully. You may now log in.")

    # ─── Password reset ───────────────────────────────────────────────────────
    async def request_password_reset(
        self, data: ForgotPasswordRequest
    ) -> MessageResponse:
        """
        Always returns success to prevent email enumeration.
        If the account exists, dispatch a reset email.
        """
        user = await self.repo.get_by_email(data.email)
        if user is not None and user.is_active:
            reset_token = create_password_reset_token(str(user.id))
            reset_url = (
                f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
            )
            try:
                from app.tasks.email_tasks import send_password_reset_email
                send_password_reset_email.delay(user.email, reset_url)
            except Exception:
                log.warning("password_reset_email_failed", email=data.email)

        return MessageResponse(
            message="If that email exists, a password reset link has been sent."
        )

    async def reset_password(self, data: ResetPasswordRequest) -> MessageResponse:
        """Validate reset token and update the user's password."""
        payload = decode_typed_token(data.token, "password_reset")

        if await is_token_blacklisted(data.token):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reset link has already been used",
            )

        user_id: str = payload.get("sub", "")
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        new_hash = hash_password(data.new_password)
        await self.repo.update_user(user_id, password_hash=new_hash)

        # One-time use — blacklist the reset token
        exp = payload.get("exp", 0)
        remaining = max(1, int(exp - datetime.now(tz=timezone.utc).timestamp()))
        await blacklist_token(data.token, remaining)

        log.info("password_reset_complete", user_id=user_id)
        return MessageResponse(message="Password updated successfully. You may now log in.")
