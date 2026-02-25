"""Create users, companies, and audit_logs tables.

Revision ID: a1b2c3d40001
Revises:
Create Date: 2026-02-25 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# ─── Revision identifiers ─────────────────────────────────────────────────────
revision: str = "a1b2c3d40001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # All DDL uses raw SQL to bypass SQLAlchemy's automatic CreateEnumType
    # calls that fire via op.create_table() even when create_type=False.

    # ── 1. user_role_enum ──────────────────────────────────────────────────────
    op.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE user_role_enum AS ENUM "
        "    ('candidate','hr','hr_admin','hiring_manager','recruiter',"
        "     'superadmin','admin','elite_admin'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; "
        "END $$;"
    ))

    # ── 2. users ───────────────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS users (
            id            UUID          NOT NULL DEFAULT gen_random_uuid(),
            email         VARCHAR(255)  NOT NULL,
            password_hash VARCHAR(255)  NOT NULL,
            full_name     VARCHAR(255)  NOT NULL,
            role          user_role_enum NOT NULL DEFAULT 'candidate',
            is_active     BOOLEAN       NOT NULL DEFAULT true,
            is_verified   BOOLEAN       NOT NULL DEFAULT false,
            created_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),
            deleted_at    TIMESTAMPTZ,
            CONSTRAINT pk_users PRIMARY KEY (id)
        )
    """))
    op.execute(sa.text(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_users_deleted_at ON users(deleted_at)"
    ))

    # ── 3. companies ───────────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS companies (
            id         UUID         NOT NULL DEFAULT gen_random_uuid(),
            name       VARCHAR(255) NOT NULL,
            industry   VARCHAR(100),
            size       VARCHAR(50),
            website    VARCHAR(500),
            hr_id      UUID,
            created_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
            CONSTRAINT pk_companies PRIMARY KEY (id),
            CONSTRAINT fk_companies_hr_id FOREIGN KEY (hr_id)
                REFERENCES users(id) ON DELETE SET NULL
        )
    """))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_companies_name ON companies(name)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_companies_hr_id ON companies(hr_id)"
    ))

    # ── 4. audit_logs ──────────────────────────────────────────────────────────
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id             UUID         NOT NULL DEFAULT gen_random_uuid(),
            user_id        UUID,
            action         VARCHAR(100) NOT NULL,
            entity_type    VARCHAR(100),
            entity_id      UUID,
            old_value_json JSONB,
            new_value_json JSONB,
            ip_address     VARCHAR(45),
            created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
            CONSTRAINT pk_audit_logs PRIMARY KEY (id),
            CONSTRAINT fk_audit_logs_user_id FOREIGN KEY (user_id)
                REFERENCES users(id) ON DELETE SET NULL
        )
    """))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs(user_id)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action)"
    ))
    op.execute(sa.text(
        "CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at)"
    ))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS audit_logs"))
    op.execute(sa.text("DROP TABLE IF EXISTS companies"))
    op.execute(sa.text("DROP TABLE IF EXISTS users"))
    op.execute(sa.text("DROP TYPE IF EXISTS user_role_enum"))
