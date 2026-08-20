"""Pydantic schemas for the `rules` endpoint."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

OntologyStatus = Literal[
    "DRAFT", "PENDING_REVIEW", "PUBLISHED", "REJECTED", "ARCHIVED"
]


class RuleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    applies_to_actions: List[Any] = Field(default_factory=list)


class RuleCreate(RuleBase):
    status: OntologyStatus = "DRAFT"
    source_refs: List[Any] = Field(default_factory=list)
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    derived_from: Optional[uuid.UUID] = None


class RuleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    applies_to_actions: Optional[List[Any]] = None
    status: Optional[OntologyStatus] = None
    source_refs: Optional[List[Any]] = None
    source_stale: Optional[bool] = None
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)


class RuleRead(RuleBase):
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


class RuleListResponse(BaseModel):
    items: List[RuleRead]
    total: int
    page: int
    page_size: int
