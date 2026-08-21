"""Router for /api/v1/extraction-jobs."""

from __future__ import annotations

import uuid
from typing import Optional

import pydantic
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.database import get_db
from app.models.extraction_jobs import ExtractionJob
from app.schemas.auth import CurrentUser
from app.schemas.extraction_jobs import (
    ExtractionJobListResponse,
    ExtractionJobRead,
)
from app.services.extraction import run_extraction_job

router = APIRouter(prefix="/extraction-jobs", tags=["Extraction Jobs"])


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------

class ExtractionJobRequest(BaseModel):
    source_type: str = "notion"  # "notion" | "text"
    source_refs: list[str]

    @pydantic.field_validator("source_type")
    @classmethod
    def _check_source_type(cls, v: str) -> str:
        if v not in ("notion", "text"):
            raise ValueError(f"source_type은 'notion' 또는 'text' 여야 합니다 (받은 값: '{v}')")
        return v


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_or_404(job_id: uuid.UUID, db: AsyncSession) -> ExtractionJob:
    result = await db.get(ExtractionJob, job_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ExtractionJob {job_id} not found",
        )
    return result


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=ExtractionJobListResponse,
    summary="List extraction jobs",
)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    job_status: Optional[str] = Query(None, alias="status"),
    source_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> ExtractionJobListResponse:
    query = select(ExtractionJob).order_by(ExtractionJob.created_at.desc())
    if job_status:
        query = query.where(ExtractionJob.status == job_status)
    if source_type:
        query = query.where(ExtractionJob.source_type == source_type)

    total: int = (
        await db.execute(select(func.count()).select_from(query.subquery()))
    ).scalar_one()

    rows = (
        await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()

    return ExtractionJobListResponse(
        items=[ExtractionJobRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    status_code=202,
    summary="Trigger extraction from Notion pages",
)
async def create_extraction_job(
    body: ExtractionJobRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Enqueue a background extraction job that fetches Notion pages, calls
    Claude Vertex AI, and saves DRAFT objects/links/actions to PostgreSQL.

    Returns HTTP 202 immediately; poll ``GET /extraction-jobs/{job_id}`` for
    progress and final status.
    """
    job = ExtractionJob(
        source_type=body.source_type,
        source_refs=body.source_refs,
        status="RUNNING",
        created_by=current_user.id,
        total_docs=len(body.source_refs),
    )
    db.add(job)
    await db.flush()
    await db.commit()

    background_tasks.add_task(run_extraction_job, job.id, body.source_refs, body.source_type)

    return {"job_id": str(job.id), "status": "RUNNING", "total_docs": len(body.source_refs)}


@router.get(
    "/{job_id}",
    response_model=ExtractionJobRead,
    summary="Get an extraction job",
)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ExtractionJobRead:
    return ExtractionJobRead.model_validate(await _get_or_404(job_id, db))
