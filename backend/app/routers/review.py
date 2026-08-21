"""Human review router — approve or reject PENDING_REVIEW ontology items.

Supports objects, links, and actions by a single UUID.
"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_domain_expert
from app.database import get_db
from app.models.actions import Action
from app.models.links import Link
from app.models.objects import Object
from app.models.rules import Rule
from app.schemas.auth import CurrentUser

router = APIRouter(prefix="/review", tags=["Review"])

REVIEWABLE_MODELS = [Object, Link, Action, Rule]


class RejectRequest(BaseModel):
    reason: str = ""


async def _find_item(item_id: uuid.UUID, db: AsyncSession) -> Any:
    """Search objects → links → actions for the given UUID."""
    for Model in REVIEWABLE_MODELS:
        result = await db.execute(select(Model).where(Model.id == item_id))
        item = result.scalar_one_or_none()
        if item is not None:
            return item
    return None


@router.post(
    "/{item_id}/approve",
    summary="Approve a PENDING_REVIEW item → PUBLISHED",
)
async def approve_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_domain_expert),
) -> dict:
    """Approve a PENDING_REVIEW object, link, or action and publish it."""
    item = await _find_item(item_id, db)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="항목을 찾을 수 없습니다")

    if item.status not in ("PENDING_REVIEW", "DRAFT"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"현재 상태({item.status})에서는 승인할 수 없습니다",
        )

    item.status = "PUBLISHED"
    await db.commit()
    return {"id": str(item.id), "status": "PUBLISHED"}


@router.post(
    "/{item_id}/reject",
    summary="Reject a PENDING_REVIEW item → REJECTED",
)
async def reject_item(
    item_id: uuid.UUID,
    body: RejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_domain_expert),
) -> dict:
    """Reject a PENDING_REVIEW object, link, or action."""
    item = await _find_item(item_id, db)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="항목을 찾을 수 없습니다")

    if item.status not in ("PENDING_REVIEW", "DRAFT"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"현재 상태({item.status})에서는 반려할 수 없습니다",
        )

    item.status = "REJECTED"
    # Store rejection reason in source_refs metadata if possible
    if hasattr(item, "source_refs") and isinstance(item.source_refs, list):
        refs = list(item.source_refs)
        refs.append({"type": "rejection", "reason": body.reason})
        item.source_refs = refs

    await db.commit()
    return {"id": str(item.id), "status": "REJECTED", "reason": body.reason}
