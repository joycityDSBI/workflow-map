"""Pydantic schemas for the `actions` endpoint."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

OntologyStatus = Literal[
    "DRAFT", "PENDING_REVIEW", "PUBLISHED", "REJECTED", "ARCHIVED"
]
ActionTrigger = Literal["manual_ui", "scheduled", "notion_webhook"]


class ActionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    actor_id: Optional[uuid.UUID] = None
    reads: List[Any] = Field(default_factory=list)
    creates: List[Any] = Field(default_factory=list)
    updates: List[Any] = Field(default_factory=list)
    preconditions: Optional[str] = None
    outcomes: Optional[str] = None
    trigger: Optional[ActionTrigger] = None


class ActionCreate(ActionBase):
    status: OntologyStatus = "DRAFT"
    source_refs: List[Any] = Field(default_factory=list)
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    derived_from: Optional[uuid.UUID] = None


class ActionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    actor_id: Optional[uuid.UUID] = None
    reads: Optional[List[Any]] = None
    creates: Optional[List[Any]] = None
    updates: Optional[List[Any]] = None
    preconditions: Optional[str] = None
    outcomes: Optional[str] = None
    trigger: Optional[ActionTrigger] = None
    status: Optional[OntologyStatus] = None
    source_refs: Optional[List[Any]] = None
    source_stale: Optional[bool] = None
    confidence: Optional[Decimal] = Field(None, ge=0, le=1)


class ActionRead(ActionBase):
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


class ActionListResponse(BaseModel):
    items: List[ActionRead]
    total: int
    page: int
    page_size: int
