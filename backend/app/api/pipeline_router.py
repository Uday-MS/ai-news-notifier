"""Pipeline API router — endpoints for AI processing pipeline."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.database.session import get_db
from app.repositories.event_repository import EventRepository
from app.repositories.processed_event_repository import ProcessedEventRepository
from app.schemas.pipeline import (
    PipelineStatusResponse,
    ProcessedEventRead,
    ProcessedEventSummary,
)
from app.services.pipeline.pipeline_service import PipelineService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


# ── List Processed Events ────────────────────────────────────────────────


@router.get("/events", response_model=None)
async def list_processed_events(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List processed events with pagination and optional status filter."""
    repo = ProcessedEventRepository(db)
    events = await repo.list_events(limit=limit, offset=offset, status=status)
    total = await repo.count_total()
    return success_response(
        data={
            "events": [
                ProcessedEventSummary.model_validate(e).model_dump()
                for e in events
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    )


# ── Process Single Event ────────────────────────────────────────────────


@router.post("/process/{event_id}", response_model=None)
async def process_single_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Process a single collected event through the AI pipeline."""
    service = PipelineService(db)
    try:
        processed = await service.process_single(event_id)
    except ValueError as exc:
        return {
            "success": False,
            "error": {"code": "NOT_FOUND", "message": str(exc)},
        }

    return success_response(
        data=ProcessedEventRead.model_validate(processed).model_dump(),
        message="Event processed successfully.",
    )


# ── Process All Unprocessed ──────────────────────────────────────────────


@router.post("/process-all", response_model=None)
async def process_all_events(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Process all unprocessed collected events through the AI pipeline."""
    service = PipelineService(db)
    summary = await service.process_all_unprocessed()
    return success_response(
        data=summary,
        message=f"Processed {summary['processed']} events.",
    )


# ── Pipeline Status ──────────────────────────────────────────────────────


@router.get("/status", response_model=None)
async def pipeline_status(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return aggregated processing statistics."""
    event_repo = EventRepository(db)
    processed_repo = ProcessedEventRepository(db)

    total_collected = await event_repo.count_events()
    total_processed = await processed_repo.count_total()
    status_counts = await processed_repo.count_by_status()

    response = PipelineStatusResponse(
        total_collected=total_collected,
        total_processed=total_processed,
        ready=status_counts.get("ready", 0),
        partial=status_counts.get("partial", 0),
        failed=status_counts.get("failed", 0),
        unprocessed=total_collected - total_processed,
    )
    return success_response(data=response.model_dump())


# ── LLM Intelligence Enrichment ─────────────────────────────────────────


@router.post("/enrich-pending", response_model=None)
async def enrich_pending_events(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Trigger LLM intelligence enrichment for pending processed events."""
    from app.ai.llm_provider import get_llm_provider
    from app.ai.intelligence_service import IntelligenceService

    provider = get_llm_provider()
    if provider is None:
        return success_response(
            data={"enriched": 0, "message": "LLM provider not configured (GEMINI_API_KEY missing)"},
            message="LLM enrichment skipped — no API key configured.",
        )

    service = IntelligenceService(db, provider)
    summary = await service.enrich_pending(limit=limit)
    await db.commit()

    return success_response(
        data=summary,
        message=f"Enriched {summary['enriched']} event(s).",
    )


@router.post("/enrich/{event_id}", response_model=None)
async def enrich_single_event(
    event_id: uuid.UUID,
    force: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Enrich a single processed event with LLM intelligence."""
    from app.ai.llm_provider import get_llm_provider
    from app.ai.intelligence_service import IntelligenceService

    provider = get_llm_provider()
    if provider is None:
        return success_response(
            data=None,
            message="LLM provider not configured (GEMINI_API_KEY missing).",
        )

    service = IntelligenceService(db, provider)
    processed = await service.enrich_single(event_id, force=force)
    await db.commit()

    if processed is None:
        return {
            "success": False,
            "error": {"code": "NOT_FOUND", "message": f"Processed event {event_id} not found."},
        }

    return success_response(
        data=ProcessedEventRead.model_validate(processed).model_dump(),
        message="Event enriched successfully.",
    )


@router.get("/intelligence-status", response_model=None)
async def intelligence_status(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return LLM intelligence enrichment statistics."""
    from sqlalchemy import func, select
    from app.models.processed_event import ProcessedEvent

    # Count by llm_status
    stmt = (
        select(
            ProcessedEvent.llm_status,
            func.count().label("count"),
        )
        .group_by(ProcessedEvent.llm_status)
    )
    result = await db.execute(stmt)
    counts: dict[str, int] = {}
    for row in result.all():
        key = row[0] if row[0] else "pending"
        counts[key] = row[1]

    total = sum(counts.values())

    return success_response(
        data={
            "total_processed_events": total,
            "pending": counts.get("pending", 0) + counts.get(None, 0),
            "processing": counts.get("processing", 0),
            "completed": counts.get("completed", 0),
            "failed": counts.get("failed", 0),
            "skipped": counts.get("skipped", 0),
            "enrichment_coverage": round(
                (counts.get("completed", 0) / total * 100) if total > 0 else 0, 1
            ),
        },
    )
