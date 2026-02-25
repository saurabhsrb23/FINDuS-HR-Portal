"""Widen resume_url to TEXT (was VARCHAR(500), too small for base64 PDFs).

Revision ID: a1b2c3d40005
Revises: a1b2c3d40004
Create Date: 2026-02-25
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d40005"
down_revision = "a1b2c3d40004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "candidate_profiles",
        "resume_url",
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "candidate_profiles",
        "resume_url",
        type_=sa.String(500),
        existing_nullable=True,
    )
