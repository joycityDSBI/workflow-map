"""Pydantic schemas for the `extraction_jobs` endpoint."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

JobStatus = Literal[
    "RUNNING", "COMPLETED", "PARTIAL_SUCCESS", "FAILED", "RATE_LIMITED"
]
SourceType = Literal["notion", "file", "text"]


class ExtractionJobCreate(BaseModel):
    source_type: SourceType
    source_refs: List[Any] = Field(default_factory=list)
    total_docs: Optional[int] = Field(None, ge=1)


class ExtractionJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: JobStatus
    source_type: SourceType
    source_refs: List[Any]
    total_docs: Optional[int]
    success_docs: int
    failed_docs: int
    error_details: List[Any]
    created_by: str
    created_at: datetime
    completed_at: Optional[datetime]


class ExtractionJobListResponse(BaseModel):
    items: List[ExtractionJobRead]
    total: int
    page: int
    page_size: int
