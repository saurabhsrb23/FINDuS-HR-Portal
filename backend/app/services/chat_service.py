"""Chat business logic — Module 9."""
from __future__ import annotations

import base64
import uuid
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import (
    ChatConversation,
    ChatMessage,
    ConversationType,
    MessageType,
    ReportStatus,
)
from app.models.user import User, UserRole
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import (
    AdminConversationOut,
    AdminReportOut,
    BanCreate,
    ChatStatsOut,
    ConversationCreate,
    ConversationOut,
    MessageCreate,
    MessageEdit,
    MessageOut,
    ReactionCreate,
    ReportCreate,
    ReportStatusUpdate,
)

log = structlog.get_logger("donehr.chat_service")

_MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
_ALLOWED_MIME = {"application/pdf", "image/jpeg", "image/png", "image/gif", "image/webp"}
_EDIT_WINDOW_SECONDS = 300  # 5 minutes

# Roles that are allowed to chat
_CHAT_ROLES = {
    UserRole.CANDIDATE,
    UserRole.HR,
    UserRole.HR_ADMIN,
    UserRole.HIRING_MANAGER,
    UserRole.RECRUITER,
}


class ChatService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = ChatRepository(db)

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _build_message_out(
        self, msg: ChatMessage, current_user_id: uuid.UUID
    ) -> MessageOut:
        sender = await self._repo.get_user(msg.sender_id)
        reactions = await self._repo.get_reactions(msg.id, current_user_id)
        read_count = await self._repo.get_read_count(msg.id)
        is_read = await self._repo.is_message_read_by(msg.id, current_user_id)

        reply_preview = None
        if msg.reply_to_id:
            parent = await self._repo.get_message(msg.reply_to_id)
            if parent:
                parent_sender = await self._repo.get_user(parent.sender_id)
                reply_preview = {
                    "id": str(parent.id),
                    "sender_name": parent_sender.full_name if parent_sender else "Unknown",
                    "content": parent.content,
                    "message_type": parent.message_type.value,
                }

        from app.schemas.chat import ReactionOut, ReplyPreview

        return MessageOut(
            id=str(msg.id),
            conversation_id=str(msg.conversation_id),
            sender_id=str(msg.sender_id),
            sender_name=sender.full_name if sender else "Unknown",
            sender_role=sender.role.value if sender else "unknown",
            content=msg.content,
            message_type=msg.message_type.value,
            file_url=msg.file_url,
            file_name=msg.file_name,
            file_size=msg.file_size,
            reply_to=ReplyPreview(**reply_preview) if reply_preview else None,
            is_edited=msg.is_edited,
            edited_at=msg.edited_at,
            is_deleted=msg.is_deleted,
            reactions=[ReactionOut(**r) for r in reactions],
            read_by_count=read_count,
            is_read=is_read,
            created_at=msg.created_at,
        )

    async def _build_conversation_out(
        self, conv: ChatConversation, current_user_id: uuid.UUID
    ) -> ConversationOut:
        participants = await self._repo.get_conversation_participants(conv.id)
        unread = await self._repo.get_unread_count(conv.id, current_user_id)
        last_msg_obj = await self._repo.get_last_message(conv.id)
        last_msg = None
        if last_msg_obj:
            last_msg = await self._build_message_out(last_msg_obj, current_user_id)

        other_participant = None
        if conv.type == ConversationType.DIRECT:
            other_parts = [p for p in participants if str(p.user_id) != str(current_user_id)]
            if other_parts:
                other_user = await self._repo.get_user(other_parts[0].user_id)
                if other_user:
                    other_participant = {
                        "id": str(other_user.id),
                        "name": other_user.full_name,
                        "role": other_user.role.value,
                    }

        title = conv.title
        if not title and conv.type == ConversationType.DIRECT and other_participant:
            title = other_participant["name"]

        return ConversationOut(
            id=str(conv.id),
            type=conv.type.value,
            title=title,
            is_archived=conv.is_archived,
            participant_count=len(participants),
            unread_count=unread,
            last_message=last_msg,
            other_participant=other_participant,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )

    async def _emit_to_conversation(
        self, event_type: str, payload: dict, conversation_id: uuid.UUID
    ) -> None:
        from app.core.chat_manager import chat_manager

        recipient_ids = await self._repo.get_participant_user_ids(conversation_id)
        await chat_manager.publish_to_recipients(event_type, payload, recipient_ids)

    # ── Conversations ──────────────────────────────────────────────────────────

    async def get_or_create_conversation(
        self, current_user: User, data: ConversationCreate
    ) -> ConversationOut:
        if data.type == ConversationType.DIRECT:
            if not data.participant_id:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="participant_id required for direct conversations",
                )
            other = await self._repo.get_user(uuid.UUID(data.participant_id))
            if not other:
                raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
            if other.id == current_user.id:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, detail="Cannot message yourself"
                )
            # Both must be chat-eligible roles
            if current_user.role not in _CHAT_ROLES or other.role not in _CHAT_ROLES:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN, detail="One or both users cannot use chat"
                )

            existing = await self._repo.get_direct_conversation(current_user.id, other.id)
            if existing:
                await self._db.commit()
                return await self._build_conversation_out(existing, current_user.id)

            conv = await self._repo.create_conversation(
                ConversationType.DIRECT, current_user.id
            )
            await self._repo.add_participant(conv.id, current_user.id, is_admin=True)
            await self._repo.add_participant(conv.id, other.id)
            await self._db.commit()
            await self._db.refresh(conv)
            return await self._build_conversation_out(conv, current_user.id)

        elif data.type == ConversationType.GROUP:
            if current_user.role not in {
                UserRole.HR, UserRole.HR_ADMIN, UserRole.HIRING_MANAGER, UserRole.RECRUITER
            }:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN, detail="Only HR roles can create group chats"
                )
            company_id = uuid.UUID(data.company_id) if data.company_id else None
            conv = await self._repo.create_conversation(
                ConversationType.GROUP,
                current_user.id,
                title=data.title or "Group Chat",
                company_id=company_id,
            )
            await self._repo.add_participant(conv.id, current_user.id, is_admin=True)
            await self._db.commit()
            await self._db.refresh(conv)
            return await self._build_conversation_out(conv, current_user.id)

        elif data.type == ConversationType.BROADCAST:
            if current_user.role not in {UserRole.HR_ADMIN, UserRole.SUPERADMIN}:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN, detail="Only admins can create broadcasts"
                )
            conv = await self._repo.create_conversation(
                ConversationType.BROADCAST,
                current_user.id,
                title=data.title or "Broadcast",
            )
            await self._repo.add_participant(conv.id, current_user.id, is_admin=True)
            await self._db.commit()
            await self._db.refresh(conv)
            return await self._build_conversation_out(conv, current_user.id)

        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid conversation type")

    async def get_inbox(self, current_user: User) -> list[ConversationOut]:
        convs = await self._repo.get_user_conversations(current_user.id)
        result = []
        for conv in convs:
            result.append(await self._build_conversation_out(conv, current_user.id))
        return result

    # ── Messages ───────────────────────────────────────────────────────────────

    async def get_messages(
        self,
        current_user: User,
        conversation_id: str,
        before_id: str | None = None,
        limit: int = 50,
    ) -> list[MessageOut]:
        conv_uuid = uuid.UUID(conversation_id)
        participant = await self._repo.get_participant(conv_uuid, current_user.id)
        if not participant:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail="Not a participant of this conversation"
            )
        before_uuid = uuid.UUID(before_id) if before_id else None
        msgs = await self._repo.get_messages(conv_uuid, before_uuid, limit)
        return [await self._build_message_out(m, current_user.id) for m in msgs]

    async def send_message(
        self, current_user: User, data: MessageCreate
    ) -> MessageOut:
        conv_uuid = uuid.UUID(data.conversation_id)
        participant = await self._repo.get_participant(conv_uuid, current_user.id)
        if not participant:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail="Not a participant of this conversation"
            )
        if await self._repo.is_user_banned(current_user.id):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail="You are banned from chat"
            )
        if not data.content and not data.file_url:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Message must have content or a file",
            )
        reply_id = uuid.UUID(data.reply_to_id) if data.reply_to_id else None
        msg = await self._repo.create_message(
            conversation_id=conv_uuid,
            sender_id=current_user.id,
            content=data.content,
            message_type=data.message_type,
            file_url=data.file_url,
            file_name=data.file_name,
            file_size=data.file_size,
            reply_to_id=reply_id,
        )
        await self._db.commit()
        await self._db.refresh(msg)
        out = await self._build_message_out(msg, current_user.id)
        # Deliver via WS to all participants
        await self._emit_to_conversation(
            "new_message", out.model_dump(mode="json"), conv_uuid
        )
        return out

    async def edit_message(
        self, current_user: User, message_id: str, data: MessageEdit
    ) -> MessageOut:
        msg = await self._repo.get_message(uuid.UUID(message_id))
        if not msg:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Message not found")
        if str(msg.sender_id) != str(current_user.id):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail="Cannot edit another user's message"
            )
        if msg.is_deleted:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="Cannot edit a deleted message"
            )
        age = (datetime.now(timezone.utc) - msg.created_at).total_seconds()
        if age > _EDIT_WINDOW_SECONDS:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="Edit window of 5 minutes has passed",
            )
        msg = await self._repo.edit_message(msg, data.content)
        await self._db.commit()
        await self._db.refresh(msg)
        out = await self._build_message_out(msg, current_user.id)
        await self._emit_to_conversation(
            "message_edited", out.model_dump(mode="json"), msg.conversation_id
        )
        return out

    async def delete_message(self, current_user: User, message_id: str) -> None:
        msg = await self._repo.get_message(uuid.UUID(message_id))
        if not msg:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Message not found")
        if str(msg.sender_id) != str(current_user.id):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail="Cannot delete another user's message"
            )
        conv_id = msg.conversation_id
        await self._repo.soft_delete_message(msg)
        await self._db.commit()
        await self._emit_to_conversation(
            "message_deleted", {"message_id": message_id}, conv_id
        )

    async def add_reaction(
        self, current_user: User, message_id: str, data: ReactionCreate
    ) -> list:
        msg = await self._repo.get_message(uuid.UUID(message_id))
        if not msg or msg.is_deleted:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Message not found")
        participant = await self._repo.get_participant(msg.conversation_id, current_user.id)
        if not participant:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail="Not a participant of this conversation"
            )
        added = await self._repo.toggle_reaction(msg.id, current_user.id, data.emoji)
        await self._db.commit()
        reactions = await self._repo.get_reactions(msg.id, current_user.id)
        await self._emit_to_conversation(
            "reaction_updated",
            {"message_id": message_id, "reactions": reactions, "added": added},
            msg.conversation_id,
        )
        return reactions

    async def report_message(
        self, current_user: User, message_id: str, data: ReportCreate
    ) -> None:
        msg = await self._repo.get_message(uuid.UUID(message_id))
        if not msg:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Message not found")
        if str(msg.sender_id) == str(current_user.id):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="Cannot report your own message"
            )
        await self._repo.create_report(msg.id, current_user.id, data.reason)
        await self._db.commit()

    async def upload_file(self, current_user: User, file: UploadFile) -> dict:
        content = await file.read()
        if len(content) > _MAX_FILE_BYTES:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size is {_MAX_FILE_BYTES // 1024 // 1024} MB",
            )
        mime = file.content_type or ""
        if mime not in _ALLOWED_MIME:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Only PDF and image files (JPEG, PNG, GIF, WebP) are allowed",
            )
        msg_type = "file" if mime == "application/pdf" else "image"
        b64 = base64.b64encode(content).decode()
        data_url = f"data:{mime};base64,{b64}"
        return {
            "file_url": data_url,
            "file_name": file.filename or "file",
            "file_size": len(content),
            "message_type": msg_type,
        }

    async def mark_read(self, current_user: User, conversation_id: str) -> None:
        conv_uuid = uuid.UUID(conversation_id)
        participant = await self._repo.get_participant(conv_uuid, current_user.id)
        if not participant:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail="Not a participant of this conversation"
            )
        await self._repo.mark_conversation_read(conv_uuid, current_user.id)
        await self._db.commit()

    async def get_total_unread(self, current_user: User) -> int:
        return await self._repo.get_total_unread(current_user.id)

    # ── Admin ──────────────────────────────────────────────────────────────────

    async def admin_list_conversations(
        self, page: int = 1, page_size: int = 50
    ) -> tuple[list[AdminConversationOut], int]:
        convs, total = await self._repo.list_all_conversations(page, page_size)
        items = []
        for conv in convs:
            participants = await self._repo.get_conversation_participants(conv.id)
            msg_count = await self._repo.count_messages_in_conversation(conv.id)
            has_reports = await self._repo.conversation_has_reports(conv.id)
            items.append(
                AdminConversationOut(
                    id=str(conv.id),
                    type=conv.type.value,
                    title=conv.title,
                    participant_count=len(participants),
                    message_count=msg_count,
                    has_reports=has_reports,
                    created_at=conv.created_at,
                )
            )
        return items, total

    async def admin_get_conversation_messages(
        self, conversation_id: str, admin_user_id: uuid.UUID
    ) -> list[MessageOut]:
        conv_uuid = uuid.UUID(conversation_id)
        conv = await self._repo.get_conversation(conv_uuid)
        if not conv:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        msgs = await self._repo.get_messages(conv_uuid, limit=100)
        return [await self._build_message_out(m, admin_user_id) for m in msgs]

    async def admin_delete_message(
        self, message_id: str, admin_user_id: uuid.UUID
    ) -> None:
        msg = await self._repo.get_message(uuid.UUID(message_id))
        if not msg:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Message not found")
        conv_id = msg.conversation_id
        await self._repo.hard_delete_message(msg)
        await self._db.commit()
        await self._emit_to_conversation(
            "message_deleted", {"message_id": message_id}, conv_id
        )

    async def admin_ban_user(self, data: BanCreate, admin_user_id: uuid.UUID) -> None:
        user = await self._repo.get_user(uuid.UUID(data.user_id))
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        await self._repo.ban_user(user.id, admin_user_id, data.reason, data.banned_until)
        await self._db.commit()

    async def admin_get_reports(
        self, page: int = 1, page_size: int = 50
    ) -> tuple[list[AdminReportOut], int]:
        reports, total = await self._repo.get_reports(page=page, page_size=page_size)
        items = []
        for r in reports:
            reporter = await self._repo.get_user(r.reporter_id)
            msg = await self._repo.get_message(r.message_id)
            items.append(
                AdminReportOut(
                    id=str(r.id),
                    message_id=str(r.message_id),
                    message_content=msg.content if msg else None,
                    reporter_name=reporter.full_name if reporter else "Unknown",
                    reason=r.reason,
                    status=r.status.value,
                    created_at=r.created_at,
                )
            )
        return items, total

    async def admin_update_report(
        self,
        report_id: str,
        data: ReportStatusUpdate,
        admin_user_id: uuid.UUID,
    ) -> None:
        await self._repo.update_report_status(
            uuid.UUID(report_id), data.status, admin_user_id
        )
        await self._db.commit()

    async def admin_get_stats(self) -> ChatStatsOut:
        messages_today = await self._repo.count_messages_today()
        unanswered = await self._repo.count_unanswered()
        return ChatStatsOut(
            messages_today=messages_today, unanswered_count=unanswered
        )

    async def search_users(self, current_user: User, query: str) -> list[dict]:
        """Search chat-eligible users by name or email (excludes self)."""
        from sqlalchemy import select, or_
        from app.models.user import User as UserModel

        q = f"%{query.lower()}%"
        result = await self._db.execute(
            select(UserModel).where(
                UserModel.id != current_user.id,
                UserModel.is_active.is_(True),
                UserModel.role.in_([r.value for r in _CHAT_ROLES]),
                or_(
                    UserModel.full_name.ilike(q),
                    UserModel.email.ilike(q),
                ),
            ).limit(20)
        )
        users = result.scalars().all()
        return [
            {"id": str(u.id), "full_name": u.full_name, "role": u.role.value}
            for u in users
        ]
