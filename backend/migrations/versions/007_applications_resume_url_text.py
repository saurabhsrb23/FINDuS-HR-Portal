"""Widen applications.resume_url to TEXT (was VARCHAR(500), too small for base64 PDFs).

Revision ID: a1b2c3d40007
Revises: a1b2c3d40006
Create Date: 2026-02-26
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d40007"
down_revision = "a1b2c3d40006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "applications",
        "resume_url",
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    # NOTE: existing rows with resume_url > 500 chars will be truncated on downgrade
    op.alter_column(
        "applications",
        "resume_url",
        type_=sa.String(500),
        existing_nullable=True,
    )
