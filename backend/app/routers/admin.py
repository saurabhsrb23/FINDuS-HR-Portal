"""Admin portal router -- all /admin/* endpoints."""
import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin_portal_role
from app.models.admin import AdminRole, AdminUser
from app.schemas.admin import (
    AdminLoginRequest,
    AdminTokenResponse,
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserResponse,
    AnnouncementRequest,
    CompanyStatusUpdate,
    PlatformOverview,
    MonitoringMetrics,
    PlatformEventListResponse,
    UserListResponse,
)
from app.services.admin_service import AdminService

log = structlog.get_logger("donehr.admin_router")

router = APIRouter(prefix="/admin", tags=["admin"])


def _svc(db: AsyncSession = Depends(get_db)) -> AdminService:
    return AdminService(db)


# -- Auth --

@router.post("/login", response_model=AdminTokenResponse)
async def admin_login(
    data: AdminLoginRequest,
    request: Request,
    svc: AdminService = Depends(_svc),
):
    return await svc.login(data, request)


@router.post("/verify-pin", status_code=status.HTTP_200_OK)
async def verify_pin(
    pin: str = Query(..., min_length=6, max_length=6),
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ELITE_ADMIN)),
    svc: AdminService = Depends(_svc),
):
    ok = await svc.verify_pin(str(admin.id), pin)
    if not ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN")
    return {"verified": True}

# -- Platform overview --

@router.get("/platform/overview", response_model=PlatformOverview)
async def platform_overview(
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ELITE_ADMIN)),
    svc: AdminService = Depends(_svc),
):
    return await svc.get_platform_overview()


@router.get("/monitoring", response_model=MonitoringMetrics)
async def monitoring(
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ELITE_ADMIN)),
    svc: AdminService = Depends(_svc),
):
    return await svc.get_monitoring_metrics()


# -- Users --

@router.get("/users/candidates", response_model=UserListResponse)
async def list_candidates(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ELITE_ADMIN)),
    svc: AdminService = Depends(_svc),
):
    return await svc.list_users(role_filter="candidate", search=search, page=page, page_size=page_size)


@router.get("/users/hr", response_model=UserListResponse)
async def list_hr_users(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ELITE_ADMIN)),
    svc: AdminService = Depends(_svc),
):
    return await svc.list_users(role_filter="hr", search=search, page=page, page_size=page_size)


@router.put("/users/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: str,
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ADMIN)),
    svc: AdminService = Depends(_svc),
):
    await svc.deactivate_user(user_id, admin)


# -- Companies --

@router.get("/companies")
async def list_companies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ELITE_ADMIN)),
    svc: AdminService = Depends(_svc),
):
    items, total = await svc.list_companies(page=page, page_size=page_size)
    return {"items": [i.model_dump() for i in items], "total": total, "page": page, "page_size": page_size}


@router.patch("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_company_status(
    company_id: str,
    data: CompanyStatusUpdate,
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ADMIN)),
    svc: AdminService = Depends(_svc),
):
    await svc.update_company_status(company_id, data, admin)

# -- Admin management --

@router.get("/admins", response_model=list[AdminUserResponse])
async def list_admins(
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.SUPERADMIN)),
    svc: AdminService = Depends(_svc),
):
    admins = await svc.list_admins()
    return [AdminUserResponse.model_validate(a) for a in admins]


@router.post("/admins", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    data: AdminUserCreate,
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ADMIN)),
    svc: AdminService = Depends(_svc),
):
    new_admin = await svc.create_admin(data, admin)
    return AdminUserResponse.model_validate(new_admin)


@router.put("/admins/{admin_id}", response_model=AdminUserResponse)
async def update_admin(
    admin_id: str,
    data: AdminUserUpdate,
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.SUPERADMIN)),
    svc: AdminService = Depends(_svc),
):
    updated = await svc.update_admin(admin_id, data, admin)
    return AdminUserResponse.model_validate(updated)


@router.delete("/admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin(
    admin_id: str,
    confirmation: str = Query(...),
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.SUPERADMIN)),
    svc: AdminService = Depends(_svc),
):
    await svc.delete_admin(admin_id, confirmation, admin)


# -- Platform events --

@router.get("/events", response_model=PlatformEventListResponse)
async def list_events(
    event_type: str | None = Query(default=None),
    actor_role: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ELITE_ADMIN)),
    svc: AdminService = Depends(_svc),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories.admin_repository import AdminRepository
    repo = AdminRepository(db)
    events, total = await repo.list_events(event_type=event_type, actor_role=actor_role, page=page, page_size=page_size)
    from app.schemas.admin import PlatformEventResponse
    return PlatformEventListResponse(
        items=[PlatformEventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
    )


# -- Announcements --

@router.post("/announcements", status_code=status.HTTP_204_NO_CONTENT)
async def send_announcement(
    data: AnnouncementRequest,
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ADMIN)),
    svc: AdminService = Depends(_svc),
):
    await svc.send_announcement(data, admin)
