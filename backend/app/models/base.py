"""Declarative Base and shared OntologyMixin.

All ontology entity tables (objects, links, actions, rules) inherit
OntologyMixin so they share an identical set of audit/workflow columns.

The superseded_by and derived_from self-referential FKs are declared with
`use_alter=True` so that Alembic / DDL can emit them as ALTER TABLE ADD
CONSTRAINT after the tables exist, avoiding circular-dependency errors during
table creation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC, TIMESTAMPTZ, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Project-wide declarative base."""

    type_annotation_map = {
        uuid.UUID: UUID(as_uuid=True),
        datetime: TIMESTAMPTZ,
        Decimal: NUMERIC(3, 2),
        dict: JSONB,
        list: JSONB,
        List[Any]: JSONB,
    }


# ---------------------------------------------------------------------------
# Status enumerations (stored as plain TEXT for flexibility / easy migration)
# ---------------------------------------------------------------------------
ONTOLOGY_STATUS = ("DRAFT", "PENDING_REVIEW", "PUBLISHED", "REJECTED", "ARCHIVED")


# ---------------------------------------------------------------------------
# OntologyMixin
# ---------------------------------------------------------------------------
class OntologyMixin:
    """Common columns shared by all ontology entity tables.

    Concrete tables must also declare `superseded_by` and `derived_from`
    columns pointing to their own table's PK because the target table name
    differs per model.  See each model for the concrete FK declarations.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
    )

    status: Mapped[str] = mapped_column(
        sa.Text,
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
    )

    source_refs: Mapped[List[Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=sa.text("'[]'::jsonb"),
    )

    source_stale: Mapped[bool] = mapped_column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.false(),
    )

    confidence: Mapped[Optional[Decimal]] = mapped_column(
        NUMERIC(3, 2),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ,
        nullable=False,
        server_default=sa.func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ,
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )


# ---------------------------------------------------------------------------
# SQLAlchemy event listener to auto-update `updated_at` on flush
# ---------------------------------------------------------------------------
@event.listens_for(Base, "before_update", propagate=True)
def _set_updated_at(mapper: Any, connection: Any, target: Any) -> None:  # noqa: ANN401
    if hasattr(target, "updated_at"):
        target.updated_at = datetime.utcnow()
