"""Chat REST endpoints — Module 9.
NOTE: Do NOT add `from __future__ import annotations` — breaks FastAPI type resolution.
"""
import uuid

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_current_user,
    get_db,
    require_admin_portal_role,
)
from app.models.admin import AdminRole, AdminUser
from app.models.user import User
from app.schemas.chat import (
    AdminConversationOut,
    AdminReportOut,
    BanCreate,
    ChatStatsOut,
    ConversationCreate,
    ConversationOut,
    FileUploadResponse,
    MessageCreate,
    MessageEdit,
    MessageOut,
    ReactionCreate,
    ReportCreate,
    ReportStatusUpdate,
)
from app.services.chat_service import ChatService

log = structlog.get_logger("donehr.chat_router")

router = APIRouter(prefix="/chat", tags=["chat"])
admin_chat_router = APIRouter(prefix="/admin/chat", tags=["admin-chat"])


def _svc(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db)


# ── User chat endpoints ────────────────────────────────────────────────────────

@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_200_OK)
async def create_or_get_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    svc: ChatService = Depends(_svc),
) -> ConversationOut:
    return await svc.get_or_create_conversation(current_user, data)


@router.get("/conversations", response_model=list[ConversationOut])
async def get_inbox(
    current_user: User = Depends(get_current_user),
    svc: ChatService = Depends(_svc),
) -> list[ConversationOut]:
    return await svc.get_inbox(current_user)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages(
    conversation_id: str,
    before_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    svc: ChatService = Depends(_svc),
) -> list[MessageOut]:
    return await svc.get_messages(current_user, conversation_id, before_id, limit)


@router.post("/conversations/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_conversation_read(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    svc: ChatService = Depends(_svc),
) -> None:
    await svc.mark_read(current_user, conversation_id)


@router.post("/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    svc: ChatService = Depends(_svc),
) -> MessageOut:
    return await svc.send_message(current_user, data)


@router.patch("/messages/{message_id}", response_model=MessageOut)
async def edit_message(
    message_id: str,
    data: MessageEdit,
    current_user: User = Depends(get_current_user),
    svc: ChatService = Depends(_svc),
) -> MessageOut:
    return await svc.edit_message(current_user, message_id, data)


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    svc: ChatService = Depends(_svc),
) -> None:
    await svc.delete_message(current_user, message_id)


@router.post("/messages/{message_id}/reactions")
async def add_reaction(
    message_id: str,
    data: ReactionCreate,
    current_user: User = Depends(get_current_user),
    svc: ChatService = Depends(_svc),
) -> list:
    """Toggle reaction; returns updated reactions list."""
    return await svc.add_reaction(current_user, message_id, data)


@router.post("/messages/{message_id}/report", status_code=status.HTTP_204_NO_CONTENT)
async def report_message(
    message_id: str,
    data: ReportCreate,
    current_user: User = Depends(get_current_user),
    svc: ChatService = Depends(_svc),
) -> None:
    await svc.report_message(current_user, message_id, data)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    svc: ChatService = Depends(_svc),
) -> FileUploadResponse:
    result = await svc.upload_file(current_user, file)
    return FileUploadResponse(**result)


@router.get("/users/search")
async def search_chat_users(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    svc: ChatService = Depends(_svc),
) -> list:
    """Search users eligible for direct chat by name/email."""
    return await svc.search_users(current_user, q)


@router.get("/unread")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    svc: ChatService = Depends(_svc),
) -> dict:
    count = await svc.get_total_unread(current_user)
    return {"unread": count}


# ── Admin chat endpoints ───────────────────────────────────────────────────────

@admin_chat_router.get("/conversations")
async def admin_list_conversations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ELITE_ADMIN)),
    svc: ChatService = Depends(_svc),
) -> dict:
    items, total = await svc.admin_list_conversations(page, page_size)
    return {
        "items": [i.model_dump(mode="json") for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@admin_chat_router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def admin_get_conversation_messages(
    conversation_id: str,
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ELITE_ADMIN)),
    svc: ChatService = Depends(_svc),
) -> list[MessageOut]:
    return await svc.admin_get_conversation_messages(conversation_id, admin.id)


@admin_chat_router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_message(
    message_id: str,
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.SUPERADMIN)),
    svc: ChatService = Depends(_svc),
) -> None:
    await svc.admin_delete_message(message_id, admin.id)


@admin_chat_router.post("/bans", status_code=status.HTTP_204_NO_CONTENT)
async def admin_ban_user(
    data: BanCreate,
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ADMIN)),
    svc: ChatService = Depends(_svc),
) -> None:
    await svc.admin_ban_user(data, admin.id)


@admin_chat_router.get("/reports")
async def admin_get_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ELITE_ADMIN)),
    svc: ChatService = Depends(_svc),
) -> dict:
    items, total = await svc.admin_get_reports(page, page_size)
    return {
        "items": [i.model_dump(mode="json") for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@admin_chat_router.patch("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_update_report(
    report_id: str,
    data: ReportStatusUpdate,
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ADMIN)),
    svc: ChatService = Depends(_svc),
) -> None:
    await svc.admin_update_report(report_id, data, admin.id)


@admin_chat_router.get("/stats", response_model=ChatStatsOut)
async def admin_chat_stats(
    admin: AdminUser = Depends(require_admin_portal_role(AdminRole.ELITE_ADMIN)),
    svc: ChatService = Depends(_svc),
) -> ChatStatsOut:
    return await svc.admin_get_stats()
