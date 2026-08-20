"""SQLAlchemy model for the `audit_log` table."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMPTZ, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    """Immutable record of every status transition on an ontology entity.

    Rows are append-only — never updated or deleted in normal operation.
    """

    __tablename__ = "audit_log"

    __table_args__ = (
        sa.CheckConstraint(
            "entity_type IN ('object','link','action','rule')",
            name="ck_audit_log_entity_type",
        ),
        sa.Index("ix_audit_log_entity", "entity_type", "entity_id"),
        sa.Index("ix_audit_log_actor_id", "actor_id"),
        sa.Index("ix_audit_log_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
    )

    entity_type: Mapped[str] = mapped_column(sa.Text, nullable=False)

    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    from_status: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)

    to_status: Mapped[str] = mapped_column(sa.Text, nullable=False)

    # Azure AD Object ID of the person who performed the action
    actor_id: Mapped[str] = mapped_column(sa.Text, nullable=False)

    actor_email: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)

    reason: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ,
        nullable=False,
        server_default=sa.func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id}"
            f" entity_type={self.entity_type!r}"
            f" entity_id={self.entity_id}"
            f" {self.from_status!r}->{self.to_status!r}>"
        )
