"""Pydantic schemas for the chat module."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.chat import ConversationType, MessageType, ReportStatus


class ReactionOut(BaseModel):
    emoji: str
    count: int
    reacted: bool


class ReplyPreview(BaseModel):
    id: str
    sender_name: str
    content: str | None
    message_type: str


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    sender_name: str
    sender_role: str
    content: str | None
    message_type: str
    file_url: str | None
    file_name: str | None
    file_size: int | None
    reply_to: ReplyPreview | None
    is_edited: bool
    edited_at: datetime | None
    is_deleted: bool
    reactions: list[ReactionOut]
    read_by_count: int
    is_read: bool
    created_at: datetime


class ConversationOut(BaseModel):
    id: str
    type: str
    title: str | None
    is_archived: bool
    participant_count: int
    unread_count: int
    last_message: MessageOut | None
    other_participant: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class ConversationCreate(BaseModel):
    participant_id: str | None = None
    type: ConversationType = ConversationType.DIRECT
    title: str | None = Field(default=None, max_length=255)
    company_id: str | None = None
    target_role: str | None = None


class MessageCreate(BaseModel):
    conversation_id: str
    content: str | None = Field(default=None, max_length=2000)
    message_type: MessageType = MessageType.TEXT
    file_url: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    reply_to_id: str | None = None


class MessageEdit(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class ReactionCreate(BaseModel):
    emoji: str = Field(..., min_length=1, max_length=10)


class ReportCreate(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500)


class FileUploadResponse(BaseModel):
    file_url: str
    file_name: str
    file_size: int
    message_type: str


class BanCreate(BaseModel):
    user_id: str
    reason: str = Field(..., min_length=5, max_length=500)
    banned_until: datetime | None = None


class ReportStatusUpdate(BaseModel):
    status: ReportStatus


class AdminConversationOut(BaseModel):
    id: str
    type: str
    title: str | None
    participant_count: int
    message_count: int
    has_reports: bool
    created_at: datetime


class AdminReportOut(BaseModel):
    id: str
    message_id: str
    message_content: str | None
    reporter_name: str
    reason: str
    status: str
    created_at: datetime


class ChatStatsOut(BaseModel):
    messages_today: int
    unanswered_count: int
