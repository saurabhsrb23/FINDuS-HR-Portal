"""Authentication router — /auth endpoints."""
from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.rate_limiter import limiter
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


def _client_ip(request: Request) -> str | None:
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None


# ─── POST /auth/register ──────────────────────────────────────────────────────
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    data: RegisterRequest,
    request: Request,
    service: AuthService = Depends(_get_service),
) -> UserResponse:
    return await service.register(data, ip_address=_client_ip(request))


# ─── POST /auth/login ─────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive JWT tokens",
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    data: LoginRequest,
    service: AuthService = Depends(_get_service),
) -> TokenResponse:
    return await service.login(data, ip_address=_client_ip(request))


# ─── POST /auth/refresh ───────────────────────────────────────────────────────
@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token and issue a new access token",
)
async def refresh(
    data: RefreshRequest,
    service: AuthService = Depends(_get_service),
) -> TokenResponse:
    return await service.refresh_token(data)


# ─── POST /auth/logout ────────────────────────────────────────────────────────
@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke access token (blacklist in Redis)",
)
async def logout(
    request: Request,
    access_token: str | None = Cookie(default=None),
    service: AuthService = Depends(_get_service),
) -> MessageResponse:
    # Accept token from Authorization header OR cookie
    token: str | None = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    elif access_token:
        token = access_token

    if not token:
        return MessageResponse(message="Logged out successfully")

    return await service.logout(token)


# ─── GET /auth/verify-email ───────────────────────────────────────────────────
@router.get(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email address from one-time link",
)
async def verify_email(
    token: str,
    service: AuthService = Depends(_get_service),
) -> MessageResponse:
    return await service.verify_email(token)


# ─── POST /auth/forgot-password ───────────────────────────────────────────────
@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request a password reset email",
)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    response: Response,
    data: ForgotPasswordRequest,
    service: AuthService = Depends(_get_service),
) -> MessageResponse:
    return await service.request_password_reset(data)


# ─── POST /auth/reset-password ────────────────────────────────────────────────
@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Submit new password using reset token",
)
async def reset_password(
    data: ResetPasswordRequest,
    service: AuthService = Depends(_get_service),
) -> MessageResponse:
    return await service.reset_password(data)


# ─── GET /auth/me ─────────────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the currently authenticated user",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)
