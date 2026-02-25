"""Module 5: AI summaries cache table.

Revision ID: a1b2c3d40004
Revises: a1b2c3d40003
Create Date: 2025-02-01 12:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d40004"
down_revision = "a1b2c3d40003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── summary_type enum ────────────────────────────────────────────────────
    op.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'summary_type_enum') THEN
                CREATE TYPE summary_type_enum AS ENUM (
                    'resume_summary',
                    'match_score',
                    'job_description',
                    'rejection_email',
                    'resume_optimizer',
                    'comparison',
                    'ranking',
                    'parsed_resume'
                );
            END IF;
        END $$;
    """))

    # ── updated_at trigger function (idempotent) ──────────────────────────────
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """))

    # ── ai_summaries table ────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS ai_summaries (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_id       UUID NOT NULL,
            entity_type     VARCHAR(50) NOT NULL,
            summary_type    summary_type_enum NOT NULL,
            content         JSONB NOT NULL DEFAULT '{}'::jsonb,
            model_used      VARCHAR(100) DEFAULT 'llama3-8b-8192',
            token_usage     INTEGER DEFAULT 0,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

            UNIQUE (entity_id, summary_type)
        );
    """))

    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_ai_summaries_entity
            ON ai_summaries (entity_id, summary_type);
    """))

    op.execute(sa.text("""
        DROP TRIGGER IF EXISTS trg_ai_summaries_updated_at ON ai_summaries;
        CREATE TRIGGER trg_ai_summaries_updated_at
            BEFORE UPDATE ON ai_summaries
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS ai_summaries CASCADE;"))
    op.execute(sa.text("DROP TYPE IF EXISTS summary_type_enum;"))
