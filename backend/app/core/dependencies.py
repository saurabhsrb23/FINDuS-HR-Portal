"""FastAPI dependency-injection helpers for auth, DB sessions, and roles."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Callable

import structlog
from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import is_token_blacklisted
from app.core.security import decode_admin_token, decode_token
from app.db.session import AsyncSessionLocal
from app.models.user import ADMIN_ROLE_HIERARCHY, User, UserRole
from app.models.admin import AdminRole, AdminUser, ADMIN_PORTAL_ROLE_HIERARCHY

log = structlog.get_logger(__name__)

# ─── Bearer scheme (optional=True so cookie fallback works) ───────────────────
_bearer = HTTPBearer(auto_error=False)


# ─── Database ─────────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session; commit on success, rollback on exception."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ─── Current user ─────────────────────────────────────────────────────────────
async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    access_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolve the authenticated user from:
      1. Authorization: Bearer <token> header (API clients)
      2. access_token httpOnly cookie (browser clients)
    Then verifies the token is not blacklisted.
    """
    # Resolve token string
    token: str | None = None
    if credentials is not None:
        token = credentials.credentials
    elif access_token is not None:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)

    # Verify token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # Blacklist check
    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token: missing subject",
        )

    # Load user from DB
    from app.repositories.user_repository import UserRepository
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    if user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account has been deleted",
        )

    return user


# ─── Role-based access ────────────────────────────────────────────────────────
def require_role(*roles: UserRole) -> Callable:
    """
    Dependency factory — restricts an endpoint to users with one of the given roles.

    Usage::

        @router.get("/jobs")
        async def list_jobs(user: User = Depends(require_role(UserRole.RECRUITER, UserRole.HR))):
            ...
    """
    async def _dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Required roles: "
                    f"{[r.value for r in roles]}"
                ),
            )
        return current_user

    return _dependency


def require_admin_role(min_role: UserRole = UserRole.ADMIN) -> Callable:
    """
    Dependency factory — validates the admin JWT (separate secret + aud claim)
    and checks the caller has at least *min_role* in the admin hierarchy.

    Usage::

        @router.delete("/users/{user_id}")
        async def delete_user(admin = Depends(require_admin_role(UserRole.SUPERADMIN))):
            ...
    """
    async def _dependency(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
        admin_token: str | None = Cookie(default=None),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        token: str | None = None
        if credentials is not None:
            token = credentials.credentials
        elif admin_token is not None:
            token = admin_token

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin authentication credentials missing",
            )

        payload = decode_admin_token(token)

        if await is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin token has been revoked",
            )

        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed admin token",
            )

        from app.repositories.user_repository import UserRepository
        repo = UserRepository(db)
        user = await repo.get_by_id(user_id)

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin user not found or inactive",
            )

        # Hierarchy check: user.role must be >= min_role
        hierarchy = ADMIN_ROLE_HIERARCHY
        if min_role not in hierarchy or user.role not in hierarchy:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient admin privilege",
            )
        if hierarchy.index(user.role) < hierarchy.index(min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires at least role: {min_role.value}",
            )

        return user

    return _dependency


# ─── Admin portal role guard ──────────────────────────────────────────────────
def require_admin_portal_role(min_role: AdminRole = AdminRole.ELITE_ADMIN) -> Callable:
    """
    Dependency factory for the admin portal.
    Validates the admin JWT and loads the AdminUser from admin_users table.
    Hierarchy: ELITE_ADMIN (0) < ADMIN (1) < SUPERADMIN (2)
    """
    async def _dependency(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
        admin_token: str | None = Cookie(default=None),
        db: AsyncSession = Depends(get_db),
    ) -> AdminUser:
        token: str | None = None
        if credentials is not None:
            token = credentials.credentials
        elif admin_token is not None:
            token = admin_token

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin portal authentication credentials missing",
            )

        payload = decode_admin_token(token)

        if await is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin token has been revoked",
            )

        admin_id: str | None = payload.get("sub")
        if not admin_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed admin token",
            )

        from app.repositories.admin_repository import AdminRepository
        repo = AdminRepository(db)
        admin = await repo.get_by_id(admin_id)

        if admin is None or not admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin user not found or inactive",
            )

        # Hierarchy check: admin.role index must be >= min_role index
        hierarchy = ADMIN_PORTAL_ROLE_HIERARCHY
        try:
            admin_level = hierarchy.index(admin.role)
            required_level = hierarchy.index(min_role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient admin privilege",
            )

        if admin_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires at least role: {min_role.value}",
            )

        return admin

    return _dependency
