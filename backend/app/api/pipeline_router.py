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
