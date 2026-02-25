"""AI Summary cache model."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base

_enum_values = lambda obj: [e.value for e in obj]  # noqa: E731


class SummaryType(str, enum.Enum):
    RESUME_SUMMARY = "resume_summary"      # 4-line candidate summary for HR
    MATCH_SCORE = "match_score"            # job-candidate match % + breakdown
    JOB_DESCRIPTION = "job_description"   # AI-generated JD
    REJECTION_EMAIL = "rejection_email"   # drafted rejection email
    RESUME_OPTIMIZER = "resume_optimizer" # tips + score for candidate
    COMPARISON = "comparison"             # multi-candidate comparison table
    RANKING = "ranking"                   # ranked applicant list for a job
    PARSED_RESUME = "parsed_resume"       # structured fields from PDF text


class AISummary(Base):
    __tablename__ = "ai_summaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # What this cache entry belongs to (e.g. application_id, candidate_id, job_id)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)

    summary_type: Mapped[SummaryType] = mapped_column(
        SAEnum(SummaryType, name="summary_type_enum", create_type=False, values_callable=_enum_values),
        nullable=False,
    )

    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), default="llama-3.1-8b-instant")
    token_usage: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
