"""Add 'text' to extraction_jobs.source_type CHECK constraint.

Revision ID: 002
Revises: 001
Create Date: 2026-08-21
"""
from __future__ import annotations

from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL: DROP the old constraint, re-create with 'text' added
    op.drop_constraint(
        "ck_extraction_jobs_source_type",
        "extraction_jobs",
        type_="check",
    )
    op.create_check_constraint(
        "ck_extraction_jobs_source_type",
        "extraction_jobs",
        "source_type IN ('notion','file','text')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_extraction_jobs_source_type",
        "extraction_jobs",
        type_="check",
    )
    op.create_check_constraint(
        "ck_extraction_jobs_source_type",
        "extraction_jobs",
        "source_type IN ('notion','file')",
    )
