"""Router for /api/v1/rules."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.rules import Rule
from app.schemas.rules import (
    RuleCreate,
    RuleListResponse,
    RuleRead,
    RuleUpdate,
)

router = APIRouter(prefix="/rules", tags=["Rules"])


async def _get_or_404(rule_id: uuid.UUID, db: AsyncSession) -> Rule:
    result = await db.get(Rule, rule_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found",
        )
    return result


@router.get("", response_model=RuleListResponse, summary="List ontology rules")
async def list_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> RuleListResponse:
    query = select(Rule)
    if status_filter:
        query = query.where(Rule.status == status_filter)

    total: int = (
        await db.execute(select(func.count()).select_from(query.subquery()))
    ).scalar_one()

    rows = (
        await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()

    return RuleListResponse(
        items=[RuleRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=RuleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an ontology rule",
)
async def create_rule(
    payload: RuleCreate,
    db: AsyncSession = Depends(get_db),
) -> RuleRead:
    rule = Rule(**payload.model_dump())
    db.add(rule)
    await db.flush()
    await db.refresh(rule)
    return RuleRead.model_validate(rule)


@router.get("/{rule_id}", response_model=RuleRead, summary="Get an ontology rule")
async def get_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RuleRead:
    return RuleRead.model_validate(await _get_or_404(rule_id, db))


@router.patch(
    "/{rule_id}",
    response_model=RuleRead,
    summary="Partially update an ontology rule",
)
async def patch_rule(
    rule_id: uuid.UUID,
    payload: RuleUpdate,
    db: AsyncSession = Depends(get_db),
) -> RuleRead:
    rule = await _get_or_404(rule_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await db.flush()
    await db.refresh(rule)
    return RuleRead.model_validate(rule)


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete an ontology rule",
)
async def delete_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    rule = await _get_or_404(rule_id, db)
    await db.delete(rule)
