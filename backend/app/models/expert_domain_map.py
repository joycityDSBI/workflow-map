"""SQLAlchemy model for the `expert_domain_map` table."""

from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMPTZ, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ExpertDomainMap(Base):
    """Maps Azure AD users to the ontology domains they are experts in."""

    __tablename__ = "expert_domain_map"

    __table_args__ = (
        sa.UniqueConstraint("expert_id", "domain_name", name="uq_expert_domain"),
        sa.Index("ix_expert_domain_expert_id", "expert_id"),
        sa.Index("ix_expert_domain_domain_name", "domain_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=sa.text("gen_random_uuid()"),
    )

    # Azure AD Object ID of the expert
    expert_id: Mapped[str] = mapped_column(sa.Text, nullable=False)

    domain_name: Mapped[str] = mapped_column(sa.Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPTZ,
        nullable=False,
        server_default=sa.func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<ExpertDomainMap id={self.id}"
            f" expert_id={self.expert_id!r}"
            f" domain={self.domain_name!r}>"
        )
