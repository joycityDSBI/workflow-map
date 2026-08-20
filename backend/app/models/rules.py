"""SQLAlchemy model for the `rules` table."""

from __future__ import annotations

import uuid
from typing import Any, List, Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, OntologyMixin


class Rule(Base, OntologyMixin):
    """A business rule that constrains or governs one or more actions."""

    __tablename__ = "rules"

    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('DRAFT','PENDING_REVIEW','PUBLISHED','REJECTED','ARCHIVED')",
            name="ck_rules_status",
        ),
    )

    # ── Domain columns ────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(sa.Text, nullable=False, index=True)

    description: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)

    applies_to_actions: Mapped[List[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
    )

    # ── Self-referential FKs ──────────────────────────────────────────────────
    superseded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey(
            "rules.id",
            name="fk_rules_superseded_by",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    derived_from: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey(
            "rules.id",
            name="fk_rules_derived_from",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    superseded_by_rule: Mapped[Optional["Rule"]] = relationship(
        "Rule",
        foreign_keys=[superseded_by],
        remote_side="Rule.id",
        backref="supersedes",
    )

    derived_from_rule: Mapped[Optional["Rule"]] = relationship(
        "Rule",
        foreign_keys=[derived_from],
        remote_side="Rule.id",
        backref="derived_versions",
    )

    def __repr__(self) -> str:
        return f"<Rule id={self.id} title={self.title!r}>"
