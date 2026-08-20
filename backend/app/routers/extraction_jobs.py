"""Router for /api/v1/extraction-jobs."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.extraction_jobs import ExtractionJob
from app.schemas.extraction_jobs import (
    ExtractionJobCreate,
    ExtractionJobListResponse,
    ExtractionJobRead,
)

router = APIRouter(prefix="/extraction-jobs", tags=["Extraction Jobs"])

# Placeholder: in production this would come from the verified Azure AD token.
_PLACEHOLDER_ACTOR_ID = "00000000-0000-0000-0000-000000000000"


async def _get_or_404(job_id: uuid.UUID, db: AsyncSession) -> ExtractionJob:
    result = await db.get(ExtractionJob, job_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ExtractionJob {job_id} not found",
        )
    return result


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
    response_model=ExtractionJobRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create (trigger) an extraction job",
)
async def create_job(
    payload: ExtractionJobCreate,
    db: AsyncSession = Depends(get_db),
) -> ExtractionJobRead:
    """Enqueue a new background extraction job.

    In production, the Azure AD token's ``oid`` claim replaces the placeholder
    actor ID and the job is handed off to a Celery / background-task worker.
    """
    job = ExtractionJob(
        **payload.model_dump(),
        created_by=_PLACEHOLDER_ACTOR_ID,
        status="RUNNING",
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return ExtractionJobRead.model_validate(job)


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
