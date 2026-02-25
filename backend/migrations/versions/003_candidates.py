"""Module 4: Candidate profiles, applications, job alerts.

Revision ID: a1b2c3d40003
Revises: a1b2c3d40002
Create Date: 2025-01-15 12:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d40003"
down_revision = "a1b2c3d40002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enums ──────────────────────────────────────────────────────────────────
    op.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'employment_type_enum') THEN
                CREATE TYPE employment_type_enum AS ENUM (
                    'full_time','part_time','contract','internship','freelance'
                );
            END IF;
        END $$;
    """))

    op.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'application_status_enum') THEN
                CREATE TYPE application_status_enum AS ENUM (
                    'applied','screening','interview','offer','hired','rejected','withdrawn'
                );
            END IF;
        END $$;
    """))

    # ── updated_at trigger function (idempotent) ───────────────────────────────
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """))

    # ── candidate_profiles ────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS candidate_profiles (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id         UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,

            full_name       VARCHAR(200),
            phone           VARCHAR(20),
            location        VARCHAR(200),
            headline        VARCHAR(300),
            summary         TEXT,
            avatar_url      VARCHAR(500),

            resume_url          VARCHAR(500),
            resume_filename     VARCHAR(255),
            resume_parsed_data  JSONB,

            desired_role            VARCHAR(200),
            desired_salary_min      INTEGER,
            desired_salary_max      INTEGER,
            desired_location        VARCHAR(200),
            open_to_remote          BOOLEAN DEFAULT TRUE,
            notice_period_days      INTEGER,
            years_of_experience     FLOAT,

            profile_strength    INTEGER DEFAULT 0,

            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """))
    op.execute(sa.text("""
        DROP TRIGGER IF EXISTS trg_candidate_profiles_updated_at ON candidate_profiles;
        CREATE TRIGGER trg_candidate_profiles_updated_at
            BEFORE UPDATE ON candidate_profiles
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """))

    # ── work_experiences ──────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS work_experiences (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            candidate_id    UUID NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,

            company_name    VARCHAR(200) NOT NULL,
            job_title       VARCHAR(200) NOT NULL,
            employment_type employment_type_enum NOT NULL DEFAULT 'full_time',
            location        VARCHAR(200),
            is_current      BOOLEAN DEFAULT FALSE,
            start_date      TIMESTAMPTZ,
            end_date        TIMESTAMPTZ,
            description     TEXT,
            achievements    JSONB
        );
    """))

    # ── educations ────────────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS educations (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            candidate_id    UUID NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,

            institution     VARCHAR(200) NOT NULL,
            degree          VARCHAR(200),
            field_of_study  VARCHAR(200),
            grade           VARCHAR(50),
            start_year      INTEGER,
            end_year        INTEGER,
            is_current      BOOLEAN DEFAULT FALSE,
            description     TEXT
        );
    """))

    # ── certifications ────────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS certifications (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            candidate_id    UUID NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,

            name            VARCHAR(200) NOT NULL,
            issuing_org     VARCHAR(200),
            issue_date      TIMESTAMPTZ,
            expiry_date     TIMESTAMPTZ,
            credential_id   VARCHAR(200),
            credential_url  VARCHAR(500)
        );
    """))

    # ── projects ──────────────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS projects (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            candidate_id    UUID NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,

            title           VARCHAR(200) NOT NULL,
            description     TEXT,
            tech_stack      JSONB,
            project_url     VARCHAR(500),
            repo_url        VARCHAR(500),
            start_date      TIMESTAMPTZ,
            end_date        TIMESTAMPTZ
        );
    """))

    # ── candidate_skills ──────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS candidate_skills (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            candidate_id    UUID NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,

            skill_name      VARCHAR(100) NOT NULL,
            proficiency     INTEGER DEFAULT 3,
            years_exp       FLOAT
        );
    """))

    # ── applications ─────────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS applications (
            id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id              UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
            candidate_id        UUID NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,

            status              application_status_enum NOT NULL DEFAULT 'applied',
            cover_letter        TEXT,
            resume_url          VARCHAR(500),
            timeline            JSONB DEFAULT '[]'::jsonb,

            hr_notes            TEXT,
            pipeline_stage_id   UUID REFERENCES pipeline_stages(id) ON DELETE SET NULL,
            rating              INTEGER,

            applied_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

            UNIQUE (job_id, candidate_id)
        );
    """))
    op.execute(sa.text("""
        DROP TRIGGER IF EXISTS trg_applications_updated_at ON applications;
        CREATE TRIGGER trg_applications_updated_at
            BEFORE UPDATE ON applications
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """))

    # ── application_answers ───────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS application_answers (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            application_id  UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
            question_id     UUID NOT NULL REFERENCES job_questions(id) ON DELETE CASCADE,
            answer_text     TEXT
        );
    """))

    # ── job_alerts ────────────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS job_alerts (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            candidate_id    UUID NOT NULL REFERENCES candidate_profiles(id) ON DELETE CASCADE,

            title           VARCHAR(200) NOT NULL,
            keywords        VARCHAR(500),
            location        VARCHAR(200),
            job_type        VARCHAR(50),
            salary_min      INTEGER,
            is_active       BOOLEAN DEFAULT TRUE,
            last_sent_at    TIMESTAMPTZ,

            created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS job_alerts CASCADE;"))
    op.execute(sa.text("DROP TABLE IF EXISTS application_answers CASCADE;"))
    op.execute(sa.text("DROP TABLE IF EXISTS applications CASCADE;"))
    op.execute(sa.text("DROP TABLE IF EXISTS candidate_skills CASCADE;"))
    op.execute(sa.text("DROP TABLE IF EXISTS projects CASCADE;"))
    op.execute(sa.text("DROP TABLE IF EXISTS certifications CASCADE;"))
    op.execute(sa.text("DROP TABLE IF EXISTS educations CASCADE;"))
    op.execute(sa.text("DROP TABLE IF EXISTS work_experiences CASCADE;"))
    op.execute(sa.text("DROP TABLE IF EXISTS candidate_profiles CASCADE;"))
    op.execute(sa.text("DROP TYPE IF EXISTS application_status_enum;"))
    op.execute(sa.text("DROP TYPE IF EXISTS employment_type_enum;"))
