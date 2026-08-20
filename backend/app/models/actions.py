"""SQLAlchemy model for the `actions` table."""

from __future__ import annotations

import uuid
from typing import Any, List, Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, OntologyMixin

TRIGGER_VALUES = ("manual_ui", "scheduled", "notion_webhook")


class Action(Base, OntologyMixin):
    """An ontology action performed by an actor object."""

    __tablename__ = "actions"

    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('DRAFT','PENDING_REVIEW','PUBLISHED','REJECTED','ARCHIVED')",
            name="ck_actions_status",
        ),
        sa.CheckConstraint(
            "trigger IN ('manual_ui','scheduled','notion_webhook') OR trigger IS NULL",
            name="ck_actions_trigger",
        ),
    )

    # ── Domain columns ────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(sa.Text, nullable=False, index=True)

    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("objects.id", name="fk_actions_actor_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    reads: Mapped[List[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
    )

    creates: Mapped[List[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
    )

    updates: Mapped[List[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
    )

    preconditions: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)

    outcomes: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)

    trigger: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)

    # ── Self-referential FKs ──────────────────────────────────────────────────
    superseded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey(
            "actions.id",
            name="fk_actions_superseded_by",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    derived_from: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey(
            "actions.id",
            name="fk_actions_derived_from",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    actor: Mapped[Optional["Object"]] = relationship(  # noqa: F821
        "Object",
        foreign_keys=[actor_id],
        back_populates="actor_actions",
    )

    superseded_by_action: Mapped[Optional["Action"]] = relationship(
        "Action",
        foreign_keys=[superseded_by],
        remote_side="Action.id",
        backref="supersedes",
    )

    derived_from_action: Mapped[Optional["Action"]] = relationship(
        "Action",
        foreign_keys=[derived_from],
        remote_side="Action.id",
        backref="derived_versions",
    )

    def __repr__(self) -> str:
        return f"<Action id={self.id} name={self.name!r} trigger={self.trigger!r}>"
