"""SQLAlchemy model for the `extraction_jobs` table."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from app.models.base import TIMESTAMPTZ
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

JOB_STATUS_VALUES = ("RUNNING", "COMPLETED", "PARTIAL_SUCCESS", "FAILED", "RATE_LIMITED")
SOURCE_TYPE_VALUES = ("notion", "file")


class ExtractionJob(Base):
    """Tracks background extraction/import jobs from Notion or uploaded files."""

    __tablename__ = "extraction_jobs"

    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('RUNNING','COMPLETED','PARTIAL_SUCCESS','FAILED','RATE_LIMITED')",
            name="ck_extraction_jobs_status",
        ),
        sa.CheckConstraint(
            "source_type IN ('notion','file')",
            name="ck_extraction_jobs_source_type",
        ),
        sa.Index("ix_extraction_jobs_created_by", "created_by"),
        sa.Index("ix_extraction_jobs_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
    )

    status: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False,
        default="RUNNING",
        server_default="RUNNING",
    )

    source_type: Mapped[str] = mapped_column(sa.Text, nullable=False)

    source_refs: Mapped[List[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
    )

    total_docs: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True)

    success_docs: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    failed_docs: Mapped[int] = mapped_column(
        sa.Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    error_details: Mapped[List[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
    )

    # Azure AD Object ID of the user who triggered the job
    created_by: Mapped[str] = mapped_column(sa.Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ,
        nullable=False,
        server_default=sa.func.now(),
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMPTZ,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<ExtractionJob id={self.id}"
            f" status={self.status!r}"
            f" source_type={self.source_type!r}>"
        )
