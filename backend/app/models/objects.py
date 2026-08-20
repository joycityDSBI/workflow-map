"""SQLAlchemy model for the `objects` table."""

from __future__ import annotations

import uuid
from typing import Any, List, Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, OntologyMixin

CATEGORY_VALUES = ("actor", "domain", "tx", "cs", "record")


class Object(Base, OntologyMixin):
    """An ontology object (actor, domain, transaction, CS, or record)."""

    __tablename__ = "objects"

    __table_args__ = (
        sa.CheckConstraint(
            "category IN ('actor','domain','tx','cs','record')",
            name="ck_objects_category",
        ),
        sa.CheckConstraint(
            "status IN ('DRAFT','PENDING_REVIEW','PUBLISHED','REJECTED','ARCHIVED')",
            name="ck_objects_status",
        ),
    )

    # ── Domain columns ────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(sa.Text, nullable=False, index=True)

    category: Mapped[str] = mapped_column(sa.Text, nullable=False)

    properties: Mapped[List[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
    )

    # ── Self-referential FKs (use_alter avoids circular DDL ordering) ─────────
    superseded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey(
            "objects.id",
            name="fk_objects_superseded_by",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    derived_from: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey(
            "objects.id",
            name="fk_objects_derived_from",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    superseded_by_obj: Mapped[Optional["Object"]] = relationship(
        "Object",
        foreign_keys=[superseded_by],
        remote_side="Object.id",
        backref="supersedes",
    )

    derived_from_obj: Mapped[Optional["Object"]] = relationship(
        "Object",
        foreign_keys=[derived_from],
        remote_side="Object.id",
        backref="derived_versions",
    )

    # Links where this object is the source
    outgoing_links: Mapped[List["Link"]] = relationship(  # noqa: F821
        "Link",
        foreign_keys="Link.from_id",
        back_populates="from_object",
        cascade="all, delete-orphan",
    )

    # Links where this object is the target
    incoming_links: Mapped[List["Link"]] = relationship(  # noqa: F821
        "Link",
        foreign_keys="Link.to_id",
        back_populates="to_object",
        cascade="all, delete-orphan",
    )

    # Actions whose actor is this object
    actor_actions: Mapped[List["Action"]] = relationship(  # noqa: F821
        "Action",
        foreign_keys="Action.actor_id",
        back_populates="actor",
    )

    def __repr__(self) -> str:
        return f"<Object id={self.id} name={self.name!r} category={self.category!r}>"
