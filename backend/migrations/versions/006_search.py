"""Module 6 — Advanced Search: saved_searches, talent_pools,
search_analytics, search_vector on candidate_profiles, GIN indexes.

Revision ID: a1b2c3d40006
Revises: a1b2c3d40005
Create Date: 2026-02-25
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "a1b2c3d40006"
down_revision = "a1b2c3d40005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── saved_searches ────────────────────────────────────────────────────────
    op.create_table(
        "saved_searches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("filters", JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_saved_searches_user_id", "saved_searches", ["user_id"])

    # ── talent_pools ──────────────────────────────────────────────────────────
    op.create_table(
        "talent_pools",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_talent_pools_user_id", "talent_pools", ["user_id"])

    # ── talent_pool_candidates ────────────────────────────────────────────────
    op.create_table(
        "talent_pool_candidates",
        sa.Column(
            "pool_id",
            UUID(as_uuid=True),
            sa.ForeignKey("talent_pools.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "candidate_id",
            UUID(as_uuid=True),
            sa.ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )

    # ── search_analytics ──────────────────────────────────────────────────────
    op.create_table(
        "search_analytics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("filters", JSONB, nullable=False, server_default="{}"),
        sa.Column("result_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "searched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_search_analytics_user_id", "search_analytics", ["user_id"])
    op.create_index("ix_search_analytics_searched_at", "search_analytics", ["searched_at"])

    # ── search_vector GENERATED STORED column + GIN index ─────────────────────
    # TSVECTOR GENERATED ALWAYS AS STORED is a Postgres 12+ feature.
    op.execute("""
        ALTER TABLE candidate_profiles
        ADD COLUMN IF NOT EXISTS search_vector TSVECTOR
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(headline, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(summary, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(desired_role, '')), 'C') ||
            setweight(to_tsvector('english', coalesce(location, '')), 'D') ||
            setweight(to_tsvector('english', coalesce(full_name, '')), 'D')
        ) STORED
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS gin_candidate_search_vector
        ON candidate_profiles USING gin(search_vector)
    """)

    # ── GIN index on candidate_skills.skill_name for fast skill lookup ────────
    op.execute("""
        CREATE INDEX IF NOT EXISTS gin_candidate_skills_name
        ON candidate_skills
        USING gin(to_tsvector('english', skill_name))
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS gin_candidate_skills_name")
    op.execute("DROP INDEX IF EXISTS gin_candidate_search_vector")
    op.execute(
        "ALTER TABLE candidate_profiles DROP COLUMN IF EXISTS search_vector"
    )
    op.drop_index("ix_search_analytics_searched_at", "search_analytics")
    op.drop_index("ix_search_analytics_user_id", "search_analytics")
    op.drop_table("search_analytics")
    op.drop_table("talent_pool_candidates")
    op.drop_index("ix_talent_pools_user_id", "talent_pools")
    op.drop_table("talent_pools")
    op.drop_index("ix_saved_searches_user_id", "saved_searches")
    op.drop_table("saved_searches")
