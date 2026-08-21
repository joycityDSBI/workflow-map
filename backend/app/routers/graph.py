"""Router for /api/v1/graph — graph-view data endpoints.

The graph endpoint aggregates published objects and links into a format
suitable for direct consumption by a graph visualisation library (e.g. React
Flow, Cytoscape, D3-force).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.links import Link
from app.models.objects import Object

router = APIRouter(prefix="/graph", tags=["Graph"])


@router.get(
    "",
    summary="Get the full ontology graph (nodes + edges)",
    response_description="Nodes (objects) and edges (links) in a graph-friendly format",
)
async def get_graph(
    status_filter: Optional[str] = Query(
        "PUBLISHED",
        alias="status",
        description="Filter by ontology status. Use 'ALL' to return every status.",
    ),
    category: Optional[str] = Query(None, description="Filter nodes by category"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Return all objects as *nodes* and all links as *edges*.

    Each node has an ``id``, ``label`` (name), ``category``, and ``data`` dict
    carrying the full object payload.  Each edge carries ``id``, ``source``
    (from_id), ``target`` (to_id), ``label``, and ``cardinality``.
    """
    # ── Nodes ─────────────────────────────────────────────────────────────────
    obj_query = select(Object)
    if status_filter and status_filter != "ALL":
        obj_query = obj_query.where(Object.status == status_filter)
    if category:
        obj_query = obj_query.where(Object.category == category)

    objects = (await db.execute(obj_query)).scalars().all()

    nodes: List[Dict[str, Any]] = [
        {
            "id": str(obj.id),
            "name": obj.name,      # frontend GraphData type expects 'name'
            "label": obj.name,     # keep for D3 compatibility
            "category": obj.category,
            "status": obj.status,  # top-level for frontend type
            "data": {
                "status": obj.status,
                "properties": obj.properties,
                "source_refs": obj.source_refs,
                "confidence": float(obj.confidence) if obj.confidence else None,
            },
        }
        for obj in objects
    ]

    # Only include edges whose both endpoints are in the fetched node set
    node_ids = {str(obj.id) for obj in objects}

    # ── Edges ─────────────────────────────────────────────────────────────────
    link_query = select(Link)
    if status_filter and status_filter != "ALL":
        link_query = link_query.where(Link.status == status_filter)

    links = (await db.execute(link_query)).scalars().all()

    edges: List[Dict[str, Any]] = [
        {
            "id": str(lnk.id),
            "source": str(lnk.from_id),
            "target": str(lnk.to_id),
            "label": lnk.label,
            "cardinality": lnk.cardinality,
            "is_derived": lnk.is_derived,
        }
        for lnk in links
        if str(lnk.from_id) in node_ids and str(lnk.to_id) in node_ids
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "status_filter": status_filter,
        },
    }
