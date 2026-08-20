"""Router for /api/v1/links."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.links import Link
from app.schemas.links import (
    LinkCreate,
    LinkListResponse,
    LinkRead,
    LinkUpdate,
)

router = APIRouter(prefix="/links", tags=["Links"])


async def _get_or_404(link_id: uuid.UUID, db: AsyncSession) -> Link:
    result = await db.get(Link, link_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Link {link_id} not found",
        )
    return result


@router.get("", response_model=LinkListResponse, summary="List ontology links")
async def list_links(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    from_id: Optional[uuid.UUID] = Query(None),
    to_id: Optional[uuid.UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> LinkListResponse:
    query = select(Link)
    if from_id:
        query = query.where(Link.from_id == from_id)
    if to_id:
        query = query.where(Link.to_id == to_id)
    if status_filter:
        query = query.where(Link.status == status_filter)

    total: int = (
        await db.execute(select(func.count()).select_from(query.subquery()))
    ).scalar_one()

    rows = (
        await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()

    return LinkListResponse(
        items=[LinkRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=LinkRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an ontology link",
)
async def create_link(
    payload: LinkCreate,
    db: AsyncSession = Depends(get_db),
) -> LinkRead:
    link = Link(**payload.model_dump())
    db.add(link)
    await db.flush()
    await db.refresh(link)
    return LinkRead.model_validate(link)


@router.get("/{link_id}", response_model=LinkRead, summary="Get an ontology link")
async def get_link(
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> LinkRead:
    return LinkRead.model_validate(await _get_or_404(link_id, db))


@router.patch(
    "/{link_id}",
    response_model=LinkRead,
    summary="Partially update an ontology link",
)
async def patch_link(
    link_id: uuid.UUID,
    payload: LinkUpdate,
    db: AsyncSession = Depends(get_db),
) -> LinkRead:
    link = await _get_or_404(link_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(link, field, value)
    await db.flush()
    await db.refresh(link)
    return LinkRead.model_validate(link)


@router.delete(
    "/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an ontology link",
)
async def delete_link(
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    link = await _get_or_404(link_id, db)
    await db.delete(link)
