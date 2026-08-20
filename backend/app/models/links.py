"""SQLAlchemy model for the `links` table."""

from __future__ import annotations

import uuid
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, OntologyMixin


class Link(Base, OntologyMixin):
    """A directed relationship between two ontology objects."""

    __tablename__ = "links"

    __table_args__ = (
        sa.CheckConstraint(
            "status IN ('DRAFT','PENDING_REVIEW','PUBLISHED','REJECTED','ARCHIVED')",
            name="ck_links_status",
        ),
        sa.Index("ix_links_from_to", "from_id", "to_id"),
    )

    # ── Domain columns ────────────────────────────────────────────────────────
    from_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("objects.id", name="fk_links_from_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    to_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("objects.id", name="fk_links_to_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    label: Mapped[str] = mapped_column(sa.Text, nullable=False)

    cardinality: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)

    is_derived: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.false(),
    )

    # ── Self-referential FKs ──────────────────────────────────────────────────
    superseded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey(
            "links.id",
            name="fk_links_superseded_by",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    derived_from: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey(
            "links.id",
            name="fk_links_derived_from",
            use_alter=True,
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    from_object: Mapped["Object"] = relationship(  # noqa: F821
        "Object",
        foreign_keys=[from_id],
        back_populates="outgoing_links",
    )

    to_object: Mapped["Object"] = relationship(  # noqa: F821
        "Object",
        foreign_keys=[to_id],
        back_populates="incoming_links",
    )

    superseded_by_link: Mapped[Optional["Link"]] = relationship(
        "Link",
        foreign_keys=[superseded_by],
        remote_side="Link.id",
        backref="supersedes",
    )

    derived_from_link: Mapped[Optional["Link"]] = relationship(
        "Link",
        foreign_keys=[derived_from],
        remote_side="Link.id",
        backref="derived_versions",
    )

    def __repr__(self) -> str:
        return (
            f"<Link id={self.id} from={self.from_id} to={self.to_id}"
            f" label={self.label!r}>"
        )
