"""Extraction pipeline: Notion → Claude Vertex AI → DRAFT objects/links/actions."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.actions import Action as OntologyAction
from app.models.extraction_jobs import ExtractionJob
from app.models.links import Link as OntologyLink
from app.models.objects import Object as OntologyObject
from app.services.claude_client import extract_ontology_from_text
from app.services.notion_client import extract_page_id, get_page_text
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"actor", "domain", "tx", "cs", "record"}
VALID_TRIGGERS = {"manual_ui", "scheduled", "notion_webhook"}
VALID_CARDINALITY = {"1:1", "1:N", "N:1", "N:M"}


# ---------------------------------------------------------------------------
# Main pipeline entry point (called as a FastAPI background task)
# ---------------------------------------------------------------------------

async def run_extraction_job(job_id: uuid.UUID, source_refs: list[str]) -> None:
    """Main extraction pipeline. Runs as a FastAPI background task.

    Opens its own DB session because BackgroundTasks execute outside the
    request lifecycle and the request's session has already been closed.
    """
    async with AsyncSessionLocal() as db:
        # Load job record
        result = await db.execute(select(ExtractionJob).where(ExtractionJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            logger.error(f"ExtractionJob {job_id} not found")
            return

        job.total_docs = len(source_refs)
        await db.flush()

        success_count = 0
        failed_count = 0
        error_details: list[dict] = []

        for ref in source_refs:
            page_id = extract_page_id(ref)
            try:
                # 1. Fetch Notion page text
                logger.info(f"[job={job_id}] Fetching Notion page: {page_id}")
                text = await get_page_text(page_id)
                if not text.strip():
                    raise ValueError("Page is empty or has no readable text")

                # 2. Extract ontology with Claude Vertex AI
                logger.info(f"[job={job_id}] Extracting ontology from page: {page_id}")
                extracted = await extract_ontology_from_text(text)

                # 3. Persist extracted items as DRAFT records
                await _save_extracted(db, extracted, ref, job_id)

                success_count += 1
                logger.info(f"[job={job_id}] Page {page_id} → OK")

            except Exception as e:
                failed_count += 1
                msg = f"Page {page_id}: {type(e).__name__}: {e}"
                logger.warning(f"[job={job_id}] {msg}")
                error_details.append({"ref": ref, "error": str(e)})

        # Update job status based on outcomes
        if failed_count == 0:
            job.status = "COMPLETED"
        elif success_count == 0:
            job.status = "FAILED"
        else:
            job.status = "PARTIAL_SUCCESS"

        job.success_docs = success_count
        job.failed_docs = failed_count
        job.error_details = error_details
        job.completed_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(
            f"[job={job_id}] Done. success={success_count} failed={failed_count} status={job.status}"
        )


# ---------------------------------------------------------------------------
# DB persistence helper
# ---------------------------------------------------------------------------

async def _save_extracted(
    db: AsyncSession,
    extracted: dict,
    source_ref: str,
    job_id: uuid.UUID,
) -> None:
    """Save extracted objects/links/actions as DRAFT items."""
    source_refs_payload = [{"type": "notion", "ref": source_ref, "job_id": str(job_id)}]

    # name → saved object UUID mapping (used for link/action resolution)
    name_to_id: dict[str, uuid.UUID] = {}

    # ------------------------------------------------------------------
    # Objects
    # ------------------------------------------------------------------
    for obj_data in extracted.get("objects", []):
        category = obj_data.get("category", "domain")
        if category not in VALID_CATEGORIES:
            category = "domain"

        confidence = _parse_confidence(obj_data.get("confidence"))

        obj = OntologyObject(
            name=obj_data.get("name", "이름없음"),
            category=category,
            properties=obj_data.get("properties", []),
            source_refs=source_refs_payload,
            confidence=confidence,
            status="DRAFT",
        )
        db.add(obj)
        await db.flush()  # populate obj.id
        name_to_id[obj_data.get("name", "")] = obj.id

    # ------------------------------------------------------------------
    # Links  (resolved by from_name / to_name → object ID)
    # ------------------------------------------------------------------
    for link_data in extracted.get("links", []):
        from_name = link_data.get("from_name", "")
        to_name = link_data.get("to_name", "")
        from_id = name_to_id.get(from_name)
        to_id = name_to_id.get(to_name)

        if not from_id or not to_id:
            logger.debug(
                f"Skipping link '{from_name}→{to_name}': object not found in this batch"
            )
            continue

        cardinality = link_data.get("cardinality", "1:N")
        if cardinality not in VALID_CARDINALITY:
            cardinality = "1:N"

        confidence = _parse_confidence(link_data.get("confidence"))

        link = OntologyLink(
            from_id=from_id,
            to_id=to_id,
            label=link_data.get("label", "관계"),
            cardinality=cardinality,
            is_derived=link_data.get("is_derived", False),
            source_refs=source_refs_payload,
            confidence=confidence,
            status="DRAFT",
        )
        db.add(link)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    for action_data in extracted.get("actions", []):
        trigger = action_data.get("trigger", "manual_ui")
        if trigger not in VALID_TRIGGERS:
            trigger = "manual_ui"

        actor_name = action_data.get("actor_name", "")
        actor_id = name_to_id.get(actor_name)  # may be None if actor not in this batch

        confidence = _parse_confidence(action_data.get("confidence"))

        action = OntologyAction(
            name=action_data.get("name", "이름없음"),
            actor_id=actor_id,
            reads=action_data.get("reads", []),
            creates=action_data.get("creates", []),
            updates=action_data.get("updates", []),
            preconditions=action_data.get("preconditions"),
            outcomes=action_data.get("outcomes"),
            trigger=trigger,
            source_refs=source_refs_payload,
            confidence=confidence,
            status="DRAFT",
        )
        db.add(action)

    await db.flush()


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _parse_confidence(value: object) -> Decimal | None:
    """Parse a confidence value into a Decimal clamped to [0.00, 1.00].

    Returns None if the value is missing or cannot be converted.
    The OntologyMixin stores confidence as NUMERIC(3, 2), so Decimal is used.
    """
    if value is None:
        return None
    try:
        clamped = max(0.0, min(1.0, float(value)))
        return Decimal(f"{clamped:.2f}")
    except (ValueError, TypeError):
        return None
