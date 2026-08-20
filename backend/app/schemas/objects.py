"""Pydantic schemas for the `objects` endpoint."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ObjectCategory = Literal["actor", "domain", "tx", "cs", "record"]
OntologyStatus = Literal[
    "DRAFT", "PENDING_REVIEW", "PUBLISHED", "REJECTED", "ARCHIVED"
]


# ---------------------------------------------------------------------------
# Shared base
# ---------------------------------------------------------------------------
class ObjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    category: ObjectCategory
    properties: List[Any] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Create / Update request bodies
# ---------------------------------------------------------------------------
class ObjectCreate(ObjectBase):
    """Request body for POST /objects."""

    status: OntologyStatus = "DRAFT"
    source_refs: List[Any] = Field(default_factory=list)
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    derived_from: Optional[uuid.UUID] = None


class ObjectUpdate(BaseModel):
    """Request body for PATCH /objects/{id}.

    All fields are optional — only supplied fields are mutated.
    """

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    category: Optional[ObjectCategory] = None
    properties: Optional[List[Any]] = None
    status: Optional[OntologyStatus] = None
    source_refs: Optional[List[Any]] = None
    source_stale: Optional[bool] = None
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------
class ObjectRead(ObjectBase):
    """Full object representation returned by the API."""

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


class ObjectListResponse(BaseModel):
    """Paginated list wrapper."""

    items: List[ObjectRead]
    total: int
    page: int
    page_size: int
