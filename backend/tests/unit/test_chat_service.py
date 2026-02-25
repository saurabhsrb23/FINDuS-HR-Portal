"""Unit tests for ChatService — Module 9."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.chat import (
    ChatConversation,
    ChatMessage,
    ConversationParticipant,
    ConversationType,
    MessageType,
)
from app.models.user import User, UserRole
from app.schemas.chat import MessageCreate, MessageEdit


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(role: str = "candidate") -> User:
    u = User()
    u.id = uuid.uuid4()
    u.email = f"user_{uuid.uuid4().hex[:6]}@test.com"
    u.full_name = "Test User"
    u.role = UserRole(role)
    u.is_active = True
    return u


def _make_conversation(conv_type: str = "direct") -> ChatConversation:
    c = ChatConversation()
    c.id = uuid.uuid4()
    c.type = ConversationType(conv_type)
    c.title = None
    c.is_archived = False
    c.created_at = datetime.now(timezone.utc)
    c.updated_at = datetime.now(timezone.utc)
    return c


def _make_message(
    sender: User,
    conv: ChatConversation,
    content: str = "Hello",
) -> ChatMessage:
    m = ChatMessage()
    m.id = uuid.uuid4()
    m.conversation_id = conv.id
    m.sender_id = sender.id
    m.content = content
    m.message_type = MessageType.TEXT
    m.is_deleted = False
    m.is_edited = False
    m.created_at = datetime.now(timezone.utc)
    return m


# ── ConversationType enum ─────────────────────────────────────────────────────

class TestConversationType:
    def test_direct_value(self):
        assert ConversationType.DIRECT.value == "direct"

    def test_group_value(self):
        assert ConversationType.GROUP.value == "group"

    def test_broadcast_value(self):
        assert ConversationType.BROADCAST.value == "broadcast"


# ── MessageType enum ──────────────────────────────────────────────────────────

class TestMessageType:
    def test_text_value(self):
        assert MessageType.TEXT.value == "text"

    def test_file_value(self):
        assert MessageType.FILE.value == "file"

    def test_image_value(self):
        assert MessageType.IMAGE.value == "image"

    def test_system_value(self):
        assert MessageType.SYSTEM.value == "system"


# ── Eligible roles ────────────────────────────────────────────────────────────

class TestChatEligibleRoles:
    """Chat is accessible to candidate, hr, hr_admin, hiring_manager, recruiter."""

    def test_candidate_eligible(self):
        from app.services.chat_service import _CHAT_ROLES
        assert UserRole.CANDIDATE in _CHAT_ROLES

    def test_hr_eligible(self):
        from app.services.chat_service import _CHAT_ROLES
        assert UserRole.HR in _CHAT_ROLES

    def test_superadmin_not_eligible(self):
        from app.services.chat_service import _CHAT_ROLES
        assert UserRole.SUPERADMIN not in _CHAT_ROLES


# ── Edit window ───────────────────────────────────────────────────────────────

class TestEditWindow:
    def test_edit_window_is_5_minutes(self):
        from app.services.chat_service import _EDIT_WINDOW_SECONDS
        assert _EDIT_WINDOW_SECONDS == 300

    def test_within_edit_window(self):
        from datetime import timedelta
        from app.services.chat_service import _EDIT_WINDOW_SECONDS
        created = datetime.now(timezone.utc) - timedelta(seconds=100)
        diff = (datetime.now(timezone.utc) - created).total_seconds()
        assert diff < _EDIT_WINDOW_SECONDS

    def test_outside_edit_window(self):
        from datetime import timedelta
        from app.services.chat_service import _EDIT_WINDOW_SECONDS
        created = datetime.now(timezone.utc) - timedelta(seconds=400)
        diff = (datetime.now(timezone.utc) - created).total_seconds()
        assert diff > _EDIT_WINDOW_SECONDS


# ── File validation ───────────────────────────────────────────────────────────

class TestFileValidation:
    def test_max_file_size(self):
        from app.services.chat_service import _MAX_FILE_BYTES
        assert _MAX_FILE_BYTES == 10 * 1024 * 1024

    def test_allowed_mime_types(self):
        from app.services.chat_service import _ALLOWED_MIME
        assert "application/pdf" in _ALLOWED_MIME
        assert "image/jpeg" in _ALLOWED_MIME
        assert "image/png" in _ALLOWED_MIME
        assert "image/gif" in _ALLOWED_MIME
        assert "image/webp" in _ALLOWED_MIME

    def test_disallowed_mime_type(self):
        from app.services.chat_service import _ALLOWED_MIME
        assert "application/exe" not in _ALLOWED_MIME
        assert "text/html" not in _ALLOWED_MIME


# ── ChatService.get_or_create_conversation ────────────────────────────────────

class TestGetOrCreateConversation:
    @pytest.mark.asyncio
    async def test_cannot_message_yourself(self):
        """Direct conversation with self → 400."""
        from fastapi import HTTPException
        from app.schemas.chat import ConversationCreate
        from app.services.chat_service import ChatService

        db = AsyncMock()
        svc = ChatService(db)
        sender = _make_user("hr")
        data = ConversationCreate(type="direct", participant_id=str(sender.id))

        with patch("app.services.chat_service.ChatRepository") as MockRepo:
            repo = MockRepo.return_value
            repo.get_user = AsyncMock(return_value=sender)
            svc._repo = repo

            with pytest.raises(HTTPException) as exc_info:
                await svc.get_or_create_conversation(sender, data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_non_chat_role_blocked(self):
        """superadmin cannot start chat → 403."""
        from fastapi import HTTPException
        from app.schemas.chat import ConversationCreate
        from app.services.chat_service import ChatService

        db = AsyncMock()
        svc = ChatService(db)
        sender = _make_user("superadmin")
        other = _make_user("hr")
        data = ConversationCreate(type="direct", participant_id=str(other.id))

        with patch("app.services.chat_service.ChatRepository") as MockRepo:
            repo = MockRepo.return_value
            repo.get_user = AsyncMock(return_value=other)
            svc._repo = repo

            with pytest.raises(HTTPException) as exc_info:
                await svc.get_or_create_conversation(sender, data)
        assert exc_info.value.status_code == 403


# ── ChatService.send_message ──────────────────────────────────────────────────

class TestSendMessage:
    @pytest.mark.asyncio
    async def test_send_message_requires_participation(self):
        """Sending to a conversation where sender is not participant → 403."""
        from fastapi import HTTPException
        from app.services.chat_service import ChatService

        db = AsyncMock()
        svc = ChatService(db)
        sender = _make_user("candidate")
        conv = _make_conversation("direct")

        with patch("app.services.chat_service.ChatRepository") as MockRepo:
            repo = MockRepo.return_value
            repo.get_participant = AsyncMock(return_value=None)
            svc._repo = repo

            with pytest.raises(HTTPException) as exc_info:
                await svc.send_message(
                    sender,
                    MessageCreate(conversation_id=str(conv.id), content="Hello"),
                )
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_send_message_banned_user_blocked(self):
        """Banned user cannot send messages → 403."""
        from fastapi import HTTPException
        from app.services.chat_service import ChatService

        db = AsyncMock()
        svc = ChatService(db)
        sender = _make_user("hr")
        fake_participant = MagicMock()

        with patch("app.services.chat_service.ChatRepository") as MockRepo:
            repo = MockRepo.return_value
            repo.get_participant = AsyncMock(return_value=fake_participant)
            repo.is_user_banned = AsyncMock(return_value=True)
            svc._repo = repo

            with pytest.raises(HTTPException) as exc_info:
                await svc.send_message(
                    sender,
                    MessageCreate(conversation_id=str(uuid.uuid4()), content="Hi"),
                )
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_send_empty_message_rejected(self):
        """Empty content with no file → 422."""
        from fastapi import HTTPException
        from app.services.chat_service import ChatService

        db = AsyncMock()
        svc = ChatService(db)
        sender = _make_user("candidate")
        fake_participant = MagicMock()

        with patch("app.services.chat_service.ChatRepository") as MockRepo:
            repo = MockRepo.return_value
            repo.get_participant = AsyncMock(return_value=fake_participant)
            repo.is_user_banned = AsyncMock(return_value=False)
            svc._repo = repo

            with pytest.raises(HTTPException) as exc_info:
                await svc.send_message(
                    sender,
                    MessageCreate(conversation_id=str(uuid.uuid4()), content=""),
                )
        assert exc_info.value.status_code == 422


# ── ChatService.edit_message ──────────────────────────────────────────────────

class TestEditMessage:
    @pytest.mark.asyncio
    async def test_edit_requires_ownership(self):
        """Editing someone else's message → 403."""
        from fastapi import HTTPException
        from app.services.chat_service import ChatService

        db = AsyncMock()
        svc = ChatService(db)
        sender = _make_user("candidate")
        other = _make_user("hr")
        conv = _make_conversation("direct")
        msg = _make_message(other, conv, "Original")

        with patch(
            "app.services.chat_service.ChatRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_message = AsyncMock(return_value=msg)
            svc._repo = repo

            with pytest.raises(HTTPException) as exc_info:
                await svc.edit_message(sender, str(msg.id), "Changed")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_edit_window_enforced(self):
        """Editing a message older than 5 minutes → 403."""
        from datetime import timedelta
        from fastapi import HTTPException
        from app.services.chat_service import ChatService

        db = AsyncMock()
        svc = ChatService(db)
        sender = _make_user("candidate")
        conv = _make_conversation("direct")
        msg = _make_message(sender, conv, "Old message")
        msg.created_at = datetime.now(timezone.utc) - timedelta(minutes=10)

        with patch("app.services.chat_service.ChatRepository") as MockRepo:
            repo = MockRepo.return_value
            repo.get_message = AsyncMock(return_value=msg)
            svc._repo = repo

            with pytest.raises(HTTPException) as exc_info:
                await svc.edit_message(sender, str(msg.id), "New content")
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_edit_deleted_message_rejected(self):
        """Editing an already-deleted message → 400."""
        from fastapi import HTTPException
        from app.services.chat_service import ChatService

        db = AsyncMock()
        svc = ChatService(db)
        sender = _make_user("candidate")
        conv = _make_conversation("direct")
        msg = _make_message(sender, conv, "Deleted")
        msg.is_deleted = True

        with patch("app.services.chat_service.ChatRepository") as MockRepo:
            repo = MockRepo.return_value
            repo.get_message = AsyncMock(return_value=msg)
            svc._repo = repo

            with pytest.raises(HTTPException) as exc_info:
                await svc.edit_message(sender, str(msg.id), "New")
        assert exc_info.value.status_code == 400


# ── ChatService.delete_message ────────────────────────────────────────────────

class TestDeleteMessage:
    @pytest.mark.asyncio
    async def test_delete_requires_ownership(self):
        """Deleting someone else's message → 403."""
        from fastapi import HTTPException
        from app.services.chat_service import ChatService

        db = AsyncMock()
        svc = ChatService(db)
        sender = _make_user("candidate")
        other = _make_user("hr")
        conv = _make_conversation("direct")
        msg = _make_message(other, conv, "Not mine")

        with patch(
            "app.services.chat_service.ChatRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_message = AsyncMock(return_value=msg)
            svc._repo = repo

            with pytest.raises(HTTPException) as exc_info:
                await svc.delete_message(sender, str(msg.id))
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_nonexistent_message(self):
        """Deleting a message that doesn't exist → 404."""
        from fastapi import HTTPException
        from app.services.chat_service import ChatService

        db = AsyncMock()
        svc = ChatService(db)
        sender = _make_user("candidate")

        with patch(
            "app.services.chat_service.ChatRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_message = AsyncMock(return_value=None)
            svc._repo = repo

            with pytest.raises(HTTPException) as exc_info:
                await svc.delete_message(sender, str(uuid.uuid4()))
        assert exc_info.value.status_code == 404


# ── ChatService.add_reaction ──────────────────────────────────────────────────

class TestAddReaction:
    @pytest.mark.asyncio
    async def test_react_to_deleted_message_rejected(self):
        """Reacting to a deleted message → 404."""
        from fastapi import HTTPException
        from app.services.chat_service import ChatService

        db = AsyncMock()
        svc = ChatService(db)
        sender = _make_user("hr")
        conv = _make_conversation("direct")
        msg = _make_message(sender, conv, "Deleted")
        msg.is_deleted = True

        with patch(
            "app.services.chat_service.ChatRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.get_message = AsyncMock(return_value=msg)
            svc._repo = repo

            with pytest.raises(HTTPException) as exc_info:
                await svc.add_reaction(sender, str(msg.id), "👍")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_react_requires_participation(self):
        """Non-participant cannot react → 403."""
        from fastapi import HTTPException
        from app.services.chat_service import ChatService

        db = AsyncMock()
        svc = ChatService(db)
        sender = _make_user("candidate")
        conv = _make_conversation("direct")
        msg = _make_message(_make_user("hr"), conv, "Message")

        with patch("app.services.chat_service.ChatRepository") as MockRepo:
            repo = MockRepo.return_value
            repo.get_message = AsyncMock(return_value=msg)
            repo.get_participant = AsyncMock(return_value=None)
            svc._repo = repo

            with pytest.raises(HTTPException) as exc_info:
                await svc.add_reaction(sender, str(msg.id), "❤️")
        assert exc_info.value.status_code == 403
