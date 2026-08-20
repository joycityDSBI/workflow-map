"""Pydantic schema registry.

Re-exports all public schema classes for convenient single-import access.
"""

from app.schemas.objects import (
    ObjectBase,
    ObjectCreate,
    ObjectUpdate,
    ObjectRead,
    ObjectListResponse,
)
from app.schemas.links import (
    LinkBase,
    LinkCreate,
    LinkUpdate,
    LinkRead,
    LinkListResponse,
)
from app.schemas.actions import (
    ActionBase,
    ActionCreate,
    ActionUpdate,
    ActionRead,
    ActionListResponse,
)
from app.schemas.rules import (
    RuleBase,
    RuleCreate,
    RuleUpdate,
    RuleRead,
    RuleListResponse,
)
from app.schemas.extraction_jobs import (
    ExtractionJobCreate,
    ExtractionJobRead,
    ExtractionJobListResponse,
)

__all__ = [
    "ObjectBase",
    "ObjectCreate",
    "ObjectUpdate",
    "ObjectRead",
    "ObjectListResponse",
    "LinkBase",
    "LinkCreate",
    "LinkUpdate",
    "LinkRead",
    "LinkListResponse",
    "ActionBase",
    "ActionCreate",
    "ActionUpdate",
    "ActionRead",
    "ActionListResponse",
    "RuleBase",
    "RuleCreate",
    "RuleUpdate",
    "RuleRead",
    "RuleListResponse",
    "ExtractionJobCreate",
    "ExtractionJobRead",
    "ExtractionJobListResponse",
]
