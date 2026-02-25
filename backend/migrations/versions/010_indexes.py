"""010 — performance indexes for all major tables."""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d40010"
down_revision = "a1b2c3d40009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── candidates ────────────────────────────────────────────────────────────
    # GIN index on the pre-existing tsvector generated column
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_candidate_profiles_search_vector "
        "ON candidate_profiles USING GIN (search_vector)"
    )
    # open_to_remote filter
    op.create_index(
        "ix_candidate_profiles_open_to_remote",
        "candidate_profiles",
        ["open_to_remote"],
        if_not_exists=True,
    )

    # ── candidate_skills ──────────────────────────────────────────────────────
    # GIN on skill_name for ILIKE skill queries (trgm recommended but GIN OK)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_candidate_skills_skill_name_lower "
        "ON candidate_skills (lower(skill_name))"
    )
    op.create_index(
        "ix_candidate_skills_candidate_id",
        "candidate_skills",
        ["candidate_id"],
        if_not_exists=True,
    )

    # ── jobs ──────────────────────────────────────────────────────────────────
    op.create_index(
        "ix_jobs_status",
        "jobs",
        ["status"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_jobs_company_id",
        "jobs",
        ["company_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_jobs_posted_by",
        "jobs",
        ["posted_by"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_jobs_status_published_at",
        "jobs",
        ["status", "published_at"],
        if_not_exists=True,
    )

    # ── applications ──────────────────────────────────────────────────────────
    op.create_index(
        "ix_applications_status",
        "applications",
        ["status"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_applications_job_id",
        "applications",
        ["job_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_applications_candidate_id",
        "applications",
        ["candidate_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_applications_job_status",
        "applications",
        ["job_id", "status"],
        if_not_exists=True,
    )

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_index(
        "ix_users_role",
        "users",
        ["role"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_users_is_active_role",
        "users",
        ["is_active", "role"],
        if_not_exists=True,
    )

    # ── ai_summaries ──────────────────────────────────────────────────────────
    op.create_index(
        "ix_ai_summaries_entity_id",
        "ai_summaries",
        ["entity_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_ai_summaries_summary_type",
        "ai_summaries",
        ["summary_type"],
        if_not_exists=True,
    )

    # ── chat_messages ─────────────────────────────────────────────────────────
    op.create_index(
        "ix_chat_messages_conversation_id",
        "chat_messages",
        ["conversation_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_chat_messages_sender_id",
        "chat_messages",
        ["sender_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_chat_messages_conversation_created",
        "chat_messages",
        ["conversation_id", "created_at"],
        if_not_exists=True,
    )

    # ── platform_events ───────────────────────────────────────────────────────
    op.create_index(
        "ix_platform_events_event_type",
        "platform_events",
        ["event_type"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_platform_events_created_at",
        "platform_events",
        ["created_at"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_platform_events_event_type_created_at",
        "platform_events",
        ["event_type", "created_at"],
        if_not_exists=True,
    )

    # ── saved_searches ────────────────────────────────────────────────────────
    op.create_index(
        "ix_saved_searches_user_id",
        "saved_searches",
        ["user_id"],
        if_not_exists=True,
    )

    # ── talent_pools ──────────────────────────────────────────────────────────
    op.create_index(
        "ix_talent_pools_user_id",
        "talent_pools",
        ["user_id"],
        if_not_exists=True,
    )

    # ── job_alerts ────────────────────────────────────────────────────────────
    op.create_index(
        "ix_job_alerts_candidate_id",
        "job_alerts",
        ["candidate_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_job_alerts_is_active",
        "job_alerts",
        ["is_active"],
        if_not_exists=True,
    )

    # ── conversation_participants ─────────────────────────────────────────────
    op.create_index(
        "ix_conv_participants_user_id",
        "conversation_participants",
        ["user_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_conv_participants_conv_user",
        "conversation_participants",
        ["conversation_id", "user_id"],
        if_not_exists=True,
    )


def downgrade() -> None:
    for idx in [
        "ix_candidate_profiles_search_vector",
        "ix_candidate_profiles_open_to_remote",
        "ix_candidate_skills_skill_name_lower",
        "ix_candidate_skills_candidate_id",
        "ix_jobs_status",
        "ix_jobs_company_id",
        "ix_jobs_posted_by",
        "ix_jobs_status_published_at",
        "ix_applications_status",
        "ix_applications_job_id",
        "ix_applications_candidate_id",
        "ix_applications_job_status",
        "ix_users_role",
        "ix_users_is_active_role",
        "ix_ai_summaries_entity_id",
        "ix_ai_summaries_summary_type",
        "ix_chat_messages_conversation_id",
        "ix_chat_messages_sender_id",
        "ix_chat_messages_conversation_created",
        "ix_platform_events_event_type",
        "ix_platform_events_created_at",
        "ix_platform_events_event_type_created_at",
        "ix_saved_searches_user_id",
        "ix_talent_pools_user_id",
        "ix_job_alerts_candidate_id",
        "ix_job_alerts_is_active",
        "ix_conv_participants_user_id",
        "ix_conv_participants_conv_user",
    ]:
        op.execute(f"DROP INDEX IF EXISTS {idx}")
