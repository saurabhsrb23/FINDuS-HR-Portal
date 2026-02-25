"""002 — Job posting tables: jobs, job_skills, job_questions, pipeline_stages.

Revision ID: 002
Revises: 001
Create Date: 2026-02-25
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d40002"
down_revision = "a1b2c3d40001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enums (idempotent DO blocks) ──────────────────────────────────────────
    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE job_status_enum AS ENUM ('draft', 'active', 'paused', 'closed');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))

    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE job_type_enum AS ENUM (
                'full_time', 'part_time', 'contract', 'internship', 'remote'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))

    op.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE question_type_enum AS ENUM (
                'text', 'yes_no', 'multiple_choice', 'rating'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))

    # ── jobs ─────────────────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS jobs (
            id                   UUID        NOT NULL DEFAULT gen_random_uuid(),
            title                VARCHAR(255) NOT NULL,
            description          TEXT,
            requirements         TEXT,
            location             VARCHAR(255),
            job_type             job_type_enum NOT NULL DEFAULT 'full_time',
            department           VARCHAR(100),
            salary_min           INTEGER,
            salary_max           INTEGER,
            currency             VARCHAR(3)  NOT NULL DEFAULT 'USD',
            experience_years_min INTEGER,
            experience_years_max INTEGER,
            status               job_status_enum NOT NULL DEFAULT 'draft',
            posted_by            UUID        REFERENCES users(id) ON DELETE SET NULL,
            company_id           UUID        REFERENCES companies(id) ON DELETE SET NULL,
            published_at         TIMESTAMPTZ,
            closed_at            TIMESTAMPTZ,
            archived_at          TIMESTAMPTZ,
            deadline             TIMESTAMPTZ,
            views_count          INTEGER     NOT NULL DEFAULT 0,
            applications_count   INTEGER     NOT NULL DEFAULT 0,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id)
        );
    """))

    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_jobs_status
            ON jobs (status);
    """))
    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_jobs_posted_by
            ON jobs (posted_by);
    """))
    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_jobs_company_id
            ON jobs (company_id);
    """))
    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_jobs_deadline
            ON jobs (deadline)
            WHERE deadline IS NOT NULL;
    """))

    # ── job_skills ────────────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS job_skills (
            id          UUID        NOT NULL DEFAULT gen_random_uuid(),
            job_id      UUID        NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            skill_name  VARCHAR(100) NOT NULL,
            is_required BOOLEAN     NOT NULL DEFAULT true,
            PRIMARY KEY (id)
        );
    """))

    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_job_skills_job_id
            ON job_skills (job_id);
    """))

    # ── job_questions ─────────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS job_questions (
            id            UUID              NOT NULL DEFAULT gen_random_uuid(),
            job_id        UUID              NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            question_text TEXT              NOT NULL,
            question_type question_type_enum NOT NULL DEFAULT 'text',
            options       JSONB,
            is_required   BOOLEAN           NOT NULL DEFAULT true,
            display_order INTEGER           NOT NULL DEFAULT 0,
            PRIMARY KEY (id)
        );
    """))

    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_job_questions_job_id
            ON job_questions (job_id);
    """))

    # ── pipeline_stages ───────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS pipeline_stages (
            id          UUID        NOT NULL DEFAULT gen_random_uuid(),
            job_id      UUID        NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            stage_name  VARCHAR(100) NOT NULL,
            stage_order INTEGER     NOT NULL DEFAULT 0,
            color       VARCHAR(7)  NOT NULL DEFAULT '#6366f1',
            is_default  BOOLEAN     NOT NULL DEFAULT false,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id)
        );
    """))

    op.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_pipeline_stages_job_id
            ON pipeline_stages (job_id);
    """))

    # ── updated_at auto-trigger for jobs ──────────────────────────────────────
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))

    op.execute(sa.text("""
        DROP TRIGGER IF EXISTS set_jobs_updated_at ON jobs;
        CREATE TRIGGER set_jobs_updated_at
            BEFORE UPDATE ON jobs
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """))


def downgrade() -> None:
    op.execute(sa.text("DROP TRIGGER IF EXISTS set_jobs_updated_at ON jobs;"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS update_updated_at_column();"))
    op.execute(sa.text("DROP TABLE IF EXISTS pipeline_stages;"))
    op.execute(sa.text("DROP TABLE IF EXISTS job_questions;"))
    op.execute(sa.text("DROP TABLE IF EXISTS job_skills;"))
    op.execute(sa.text("DROP TABLE IF EXISTS jobs;"))
    op.execute(sa.text("DROP TYPE IF EXISTS question_type_enum;"))
    op.execute(sa.text("DROP TYPE IF EXISTS job_type_enum;"))
    op.execute(sa.text("DROP TYPE IF EXISTS job_status_enum;"))
