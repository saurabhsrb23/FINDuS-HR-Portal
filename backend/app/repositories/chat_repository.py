"""Repository for chat data access — Module 9."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import (
    ChatBan,
    ChatConversation,
    ChatMessage,
    ChatMessageRead,
    ChatReaction,
    ChatReport,
    ConversationParticipant,
    ConversationType,
    MessageType,
    ReportStatus,
)
from app.models.user import User


class ChatRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Conversations ──────────────────────────────────────────────────────────

    async def get_direct_conversation(
        self, user_a: uuid.UUID, user_b: uuid.UUID
    ) -> ChatConversation | None:
        a_q = select(ConversationParticipant.conversation_id).where(
            ConversationParticipant.user_id == user_a
        )
        b_q = select(ConversationParticipant.conversation_id).where(
            ConversationParticipant.user_id == user_b
        )
        q = select(ChatConversation).where(
            ChatConversation.id.in_(a_q),
            ChatConversation.id.in_(b_q),
            ChatConversation.type == ConversationType.DIRECT,
        )
        result = await self._db.execute(q)
        return result.scalar_one_or_none()

    async def create_conversation(
        self,
        type: ConversationType,
        creator_id: uuid.UUID,
        title: str | None = None,
        company_id: uuid.UUID | None = None,
    ) -> ChatConversation:
        conv = ChatConversation(
            type=type,
            creator_id=creator_id,
            title=title,
            company_id=company_id,
        )
        self._db.add(conv)
        await self._db.flush()
        return conv

    async def add_participant(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        is_admin: bool = False,
    ) -> ConversationParticipant:
        p = ConversationParticipant(
            conversation_id=conversation_id,
            user_id=user_id,
            is_admin=is_admin,
        )
        self._db.add(p)
        await self._db.flush()
        return p

    async def get_participant(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> ConversationParticipant | None:
        q = select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id,
        )
        result = await self._db.execute(q)
        return result.scalar_one_or_none()

    async def get_conversation(self, conversation_id: uuid.UUID) -> ChatConversation | None:
        q = select(ChatConversation).where(ChatConversation.id == conversation_id)
        result = await self._db.execute(q)
        return result.scalar_one_or_none()

    async def get_user_conversations(
        self, user_id: uuid.UUID
    ) -> list[ChatConversation]:
        q = (
            select(ChatConversation)
            .join(
                ConversationParticipant,
                ConversationParticipant.conversation_id == ChatConversation.id,
            )
            .where(
                ConversationParticipant.user_id == user_id,
                ConversationParticipant.is_archived == False,  # noqa: E712
            )
            .order_by(desc(ChatConversation.updated_at))
        )
        result = await self._db.execute(q)
        return list(result.scalars().all())

    async def get_conversation_participants(
        self, conversation_id: uuid.UUID
    ) -> list[ConversationParticipant]:
        q = select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id
        )
        result = await self._db.execute(q)
        return list(result.scalars().all())

    async def get_participant_user_ids(self, conversation_id: uuid.UUID) -> list[str]:
        q = select(ConversationParticipant.user_id).where(
            ConversationParticipant.conversation_id == conversation_id
        )
        result = await self._db.execute(q)
        return [str(row) for row in result.scalars().all()]

    async def touch_conversation(self, conversation_id: uuid.UUID) -> None:
        conv = await self.get_conversation(conversation_id)
        if conv:
            conv.updated_at = datetime.now(timezone.utc)
            self._db.add(conv)

    # ── Messages ───────────────────────────────────────────────────────────────

    async def create_message(
        self,
        conversation_id: uuid.UUID,
        sender_id: uuid.UUID,
        content: str | None,
        message_type: MessageType = MessageType.TEXT,
        file_url: str | None = None,
        file_name: str | None = None,
        file_size: int | None = None,
        reply_to_id: uuid.UUID | None = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            file_url=file_url,
            file_name=file_name,
            file_size=file_size,
            reply_to_id=reply_to_id,
        )
        self._db.add(msg)
        await self._db.flush()
        await self.touch_conversation(conversation_id)
        return msg

    async def get_message(self, message_id: uuid.UUID) -> ChatMessage | None:
        q = select(ChatMessage).where(ChatMessage.id == message_id)
        result = await self._db.execute(q)
        return result.scalar_one_or_none()

    async def get_messages(
        self,
        conversation_id: uuid.UUID,
        before_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[ChatMessage]:
        q = select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
        if before_id:
            anchor = await self.get_message(before_id)
            if anchor:
                q = q.where(ChatMessage.created_at < anchor.created_at)
        q = q.order_by(desc(ChatMessage.created_at)).limit(limit)
        result = await self._db.execute(q)
        msgs = list(result.scalars().all())
        return list(reversed(msgs))  # oldest first

    async def edit_message(self, msg: ChatMessage, content: str) -> ChatMessage:
        msg.content = content
        msg.is_edited = True
        msg.edited_at = datetime.now(timezone.utc)
        self._db.add(msg)
        await self._db.flush()
        return msg

    async def soft_delete_message(self, msg: ChatMessage) -> ChatMessage:
        msg.is_deleted = True
        msg.deleted_at = datetime.now(timezone.utc)
        msg.content = None
        self._db.add(msg)
        await self._db.flush()
        return msg

    async def hard_delete_message(self, msg: ChatMessage) -> None:
        await self._db.delete(msg)
        await self._db.flush()

    async def get_last_message(self, conversation_id: uuid.UUID) -> ChatMessage | None:
        q = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(1)
        )
        result = await self._db.execute(q)
        return result.scalar_one_or_none()

    # ── Read receipts ──────────────────────────────────────────────────────────

    async def mark_read(self, message_id: uuid.UUID, user_id: uuid.UUID) -> None:
        existing = await self._db.execute(
            select(ChatMessageRead).where(
                ChatMessageRead.message_id == message_id,
                ChatMessageRead.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none() is None:
            self._db.add(ChatMessageRead(message_id=message_id, user_id=user_id))
            await self._db.flush()

    async def mark_conversation_read(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        msgs = await self.get_messages(conversation_id, limit=200)
        for msg in msgs:
            if str(msg.sender_id) != str(user_id):
                await self.mark_read(msg.id, user_id)
        p = await self.get_participant(conversation_id, user_id)
        if p:
            p.last_read_at = datetime.now(timezone.utc)
            self._db.add(p)
        await self._db.flush()

    async def is_message_read_by(self, message_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        q = select(ChatMessageRead).where(
            ChatMessageRead.message_id == message_id,
            ChatMessageRead.user_id == user_id,
        )
        result = await self._db.execute(q)
        return result.scalar_one_or_none() is not None

    async def get_read_count(self, message_id: uuid.UUID) -> int:
        q = select(func.count(ChatMessageRead.id)).where(
            ChatMessageRead.message_id == message_id
        )
        result = await self._db.execute(q)
        return result.scalar_one() or 0

    async def get_unread_count(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> int:
        read_ids = select(ChatMessageRead.message_id).where(
            ChatMessageRead.user_id == user_id
        )
        q = select(func.count(ChatMessage.id)).where(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.sender_id != user_id,
            ChatMessage.is_deleted == False,  # noqa: E712
            ChatMessage.id.not_in(read_ids),
        )
        result = await self._db.execute(q)
        return result.scalar_one() or 0

    async def get_total_unread(self, user_id: uuid.UUID) -> int:
        convs = await self.get_user_conversations(user_id)
        total = 0
        for conv in convs:
            total += await self.get_unread_count(conv.id, user_id)
        return total

    # ── Reactions ──────────────────────────────────────────────────────────────

    async def toggle_reaction(
        self, message_id: uuid.UUID, user_id: uuid.UUID, emoji: str
    ) -> bool:
        """Add reaction if not present, remove if present. Returns True if added."""
        q = select(ChatReaction).where(
            ChatReaction.message_id == message_id,
            ChatReaction.user_id == user_id,
            ChatReaction.emoji == emoji,
        )
        existing = (await self._db.execute(q)).scalar_one_or_none()
        if existing:
            await self._db.delete(existing)
            await self._db.flush()
            return False
        self._db.add(ChatReaction(message_id=message_id, user_id=user_id, emoji=emoji))
        await self._db.flush()
        return True

    async def get_reactions(
        self, message_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> list[dict]:
        q = select(ChatReaction).where(ChatReaction.message_id == message_id)
        result = await self._db.execute(q)
        reactions = list(result.scalars().all())
        grouped: dict[str, dict] = {}
        for r in reactions:
            if r.emoji not in grouped:
                grouped[r.emoji] = {"emoji": r.emoji, "count": 0, "reacted": False}
            grouped[r.emoji]["count"] += 1
            if str(r.user_id) == str(current_user_id):
                grouped[r.emoji]["reacted"] = True
        return list(grouped.values())

    # ── Reports ────────────────────────────────────────────────────────────────

    async def create_report(
        self, message_id: uuid.UUID, reporter_id: uuid.UUID, reason: str
    ) -> ChatReport:
        report = ChatReport(
            message_id=message_id, reporter_id=reporter_id, reason=reason
        )
        self._db.add(report)
        await self._db.flush()
        return report

    async def get_reports(
        self, status: str | None = None, page: int = 1, page_size: int = 50
    ) -> tuple[list[ChatReport], int]:
        q = select(ChatReport)
        if status:
            q = q.where(ChatReport.status == status)
        count_q = select(func.count()).select_from(q.subquery())
        total = (await self._db.execute(count_q)).scalar_one()
        result = await self._db.execute(
            q.order_by(desc(ChatReport.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_report(self, report_id: uuid.UUID) -> ChatReport | None:
        q = select(ChatReport).where(ChatReport.id == report_id)
        return (await self._db.execute(q)).scalar_one_or_none()

    async def update_report_status(
        self,
        report_id: uuid.UUID,
        status: ReportStatus,
        reviewed_by: uuid.UUID,
    ) -> None:
        report = await self.get_report(report_id)
        if report:
            report.status = status
            report.reviewed_by = reviewed_by
            report.reviewed_at = datetime.now(timezone.utc)
            self._db.add(report)
            await self._db.flush()

    # ── Bans ───────────────────────────────────────────────────────────────────

    async def ban_user(
        self,
        user_id: uuid.UUID,
        banned_by: uuid.UUID,
        reason: str,
        banned_until: datetime | None,
    ) -> ChatBan:
        # Deactivate existing bans
        existing_q = select(ChatBan).where(
            ChatBan.user_id == user_id, ChatBan.is_active == True  # noqa: E712
        )
        existing = (await self._db.execute(existing_q)).scalars().all()
        for b in existing:
            b.is_active = False
            self._db.add(b)
        ban = ChatBan(
            user_id=user_id,
            banned_by=banned_by,
            reason=reason,
            banned_until=banned_until,
        )
        self._db.add(ban)
        await self._db.flush()
        return ban

    async def is_user_banned(self, user_id: uuid.UUID) -> bool:
        now = datetime.now(timezone.utc)
        q = select(ChatBan).where(
            ChatBan.user_id == user_id,
            ChatBan.is_active == True,  # noqa: E712
            or_(ChatBan.banned_until.is_(None), ChatBan.banned_until > now),
        )
        result = await self._db.execute(q)
        return result.scalar_one_or_none() is not None

    # ── Admin ──────────────────────────────────────────────────────────────────

    async def list_all_conversations(
        self, page: int = 1, page_size: int = 50
    ) -> tuple[list[ChatConversation], int]:
        q = select(ChatConversation)
        count_q = select(func.count()).select_from(q.subquery())
        total = (await self._db.execute(count_q)).scalar_one()
        result = await self._db.execute(
            q.order_by(desc(ChatConversation.updated_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def count_messages_in_conversation(self, conversation_id: uuid.UUID) -> int:
        q = select(func.count(ChatMessage.id)).where(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.is_deleted == False,  # noqa: E712
        )
        return (await self._db.execute(q)).scalar_one() or 0

    async def conversation_has_reports(self, conversation_id: uuid.UUID) -> bool:
        msgs_q = select(ChatMessage.id).where(
            ChatMessage.conversation_id == conversation_id
        )
        q = select(ChatReport).where(
            ChatReport.message_id.in_(msgs_q),
            ChatReport.status == ReportStatus.PENDING,
        )
        return (await self._db.execute(q)).scalar_one_or_none() is not None

    async def count_messages_today(self) -> int:
        today = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        q = select(func.count(ChatMessage.id)).where(
            ChatMessage.created_at >= today
        )
        return (await self._db.execute(q)).scalar_one() or 0

    async def count_unanswered(self) -> int:
        from app.models.user import UserRole

        q = select(func.count()).select_from(
            select(ChatConversation.id)
            .join(ChatMessage, ChatMessage.conversation_id == ChatConversation.id)
            .join(User, User.id == ChatMessage.sender_id)
            .where(
                User.role == UserRole.CANDIDATE,
                ChatConversation.type == ConversationType.DIRECT,
            )
            .distinct()
            .subquery()
        )
        return (await self._db.execute(q)).scalar_one() or 0

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
