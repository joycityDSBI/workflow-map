"""Pydantic schemas for the `links` endpoint."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

OntologyStatus = Literal[
    "DRAFT", "PENDING_REVIEW", "PUBLISHED", "REJECTED", "ARCHIVED"
]


class LinkBase(BaseModel):
    from_id: uuid.UUID
    to_id: uuid.UUID
    label: str = Field(..., min_length=1, max_length=500)
    cardinality: Optional[str] = Field(
        None,
        examples=["1:1", "1:N", "N:M"],
        max_length=20,
    )
    is_derived: bool = False


class LinkCreate(LinkBase):
    status: OntologyStatus = "DRAFT"
    source_refs: List[Any] = Field(default_factory=list)
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    derived_from: Optional[uuid.UUID] = None


class LinkUpdate(BaseModel):
    label: Optional[str] = Field(None, min_length=1, max_length=500)
    cardinality: Optional[str] = Field(None, max_length=20)
    is_derived: Optional[bool] = None
    status: Optional[OntologyStatus] = None
    source_refs: Optional[List[Any]] = None
    source_stale: Optional[bool] = None
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)


class LinkRead(LinkBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: OntologyStatus
    source_refs: List[Any]
    source_stale: bool
    confidence: Optional[Decimal]
    superseded_by: Optional[uuid.UUID]
    derived_from: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime


class LinkListResponse(BaseModel):
    items: List[LinkRead]
    total: int
    page: int
    page_size: int
