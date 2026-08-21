"""Router for /api/v1/actions."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.actions import Action
from app.schemas.actions import (
    ActionCreate,
    ActionListResponse,
    ActionRead,
    ActionUpdate,
)

router = APIRouter(prefix="/actions", tags=["Actions"])


async def _get_or_404(action_id: uuid.UUID, db: AsyncSession) -> Action:
    result = await db.get(Action, action_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action {action_id} not found",
        )
    return result


@router.get("", response_model=ActionListResponse, summary="List ontology actions")
async def list_actions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    actor_id: Optional[uuid.UUID] = Query(None),
    trigger: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> ActionListResponse:
    query = select(Action)
    if actor_id:
        query = query.where(Action.actor_id == actor_id)
    if trigger:
        query = query.where(Action.trigger == trigger)
    if status_filter:
        query = query.where(Action.status == status_filter)

    total: int = (
        await db.execute(select(func.count()).select_from(query.subquery()))
    ).scalar_one()

    rows = (
        await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()

    return ActionListResponse(
        items=[ActionRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=ActionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an ontology action",
)
async def create_action(
    payload: ActionCreate,
    db: AsyncSession = Depends(get_db),
) -> ActionRead:
    action = Action(**payload.model_dump())
    db.add(action)
    await db.flush()
    await db.refresh(action)
    return ActionRead.model_validate(action)


@router.get("/{action_id}", response_model=ActionRead, summary="Get an ontology action")
async def get_action(
    action_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ActionRead:
    return ActionRead.model_validate(await _get_or_404(action_id, db))


@router.patch(
    "/{action_id}",
    response_model=ActionRead,
    summary="Partially update an ontology action",
)
async def patch_action(
    action_id: uuid.UUID,
    payload: ActionUpdate,
    db: AsyncSession = Depends(get_db),
) -> ActionRead:
    action = await _get_or_404(action_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(action, field, value)
    await db.flush()
    await db.refresh(action)
    return ActionRead.model_validate(action)


@router.delete(
    "/{action_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete an ontology action",
)
async def delete_action(
    action_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    action = await _get_or_404(action_id, db)
    await db.delete(action)
