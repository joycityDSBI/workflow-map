"""Router for /api/v1/objects."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.objects import Object
from app.schemas.objects import (
    ObjectCreate,
    ObjectListResponse,
    ObjectRead,
    ObjectUpdate,
)

router = APIRouter(prefix="/objects", tags=["Objects"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _get_or_404(object_id: uuid.UUID, db: AsyncSession) -> Object:
    result = await db.get(Object, object_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Object {object_id} not found",
        )
    return result


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get("", response_model=ObjectListResponse, summary="List ontology objects")
async def list_objects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> ObjectListResponse:
    """Return a paginated list of ontology objects with optional filters."""
    query = select(Object)
    if category:
        query = query.where(Object.category == category)
    if status_filter:
        query = query.where(Object.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total: int = (await db.execute(count_query)).scalar_one()

    query = query.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(query)).scalars().all()

    return ObjectListResponse(
        items=[ObjectRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=ObjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an ontology object",
)
async def create_object(
    payload: ObjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ObjectRead:
    obj = Object(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return ObjectRead.model_validate(obj)


@router.get("/{object_id}", response_model=ObjectRead, summary="Get an ontology object")
async def get_object(
    object_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ObjectRead:
    obj = await _get_or_404(object_id, db)
    return ObjectRead.model_validate(obj)


@router.patch(
    "/{object_id}",
    response_model=ObjectRead,
    summary="Partially update an ontology object",
)
async def patch_object(
    object_id: uuid.UUID,
    payload: ObjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ObjectRead:
    obj = await _get_or_404(object_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    return ObjectRead.model_validate(obj)


@router.delete(
    "/{object_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete an ontology object",
)
async def delete_object(
    object_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    obj = await _get_or_404(object_id, db)
    await db.delete(obj)
    await db.commit()
    return Response(status_code=204)
