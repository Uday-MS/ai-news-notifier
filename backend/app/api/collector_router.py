"""Collector API router — endpoints for managing sources and triggering runs."""

from __future__ import annotations

import uuid
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.registry import collector_registry
from app.core.responses import success_response
from app.database.session import get_db
from app.repositories.collector_source_repository import CollectorSourceRepository
from app.repositories.event_repository import EventRepository
from app.schemas.collector_source import (
    CollectorSourceCreate,
    CollectorSourceHealth,
    CollectorSourceRead,
)
from app.schemas.event import EventSummary
from app.services.collector_service import CollectorService

router = APIRouter(prefix="/collectors", tags=["collectors"])


# ── Collector Types ──────────────────────────────────────────────────────


@router.get("/types")
async def list_collector_types() -> dict[str, Any]:
    """Return all registered collector type identifiers."""
    return success_response(data=collector_registry.list_types())


# ── Sources CRUD ─────────────────────────────────────────────────────────


@router.get("/sources", response_model=None)
async def list_sources(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """List all registered collector sources."""
    repo = CollectorSourceRepository(db)
    sources = await repo.list_all()
    return success_response(
        data=[CollectorSourceRead.model_validate(s).model_dump() for s in sources]
    )


@router.post("/sources", response_model=None, status_code=201)
async def create_source(
    payload: CollectorSourceCreate,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Register a new collector source."""
    # Validate that the collector type exists
    if collector_registry.get(payload.collector_type) is None:
        return {
            "success": False,
            "error": {
                "code": "INVALID_COLLECTOR_TYPE",
                "message": f"Unknown collector type: {payload.collector_type}",
            },
        }

    repo = CollectorSourceRepository(db)
    source = await repo.create(**payload.model_dump())
    return success_response(
        data=CollectorSourceRead.model_validate(source).model_dump(),
        message="Source registered successfully.",
    )


# ── Run Collectors ───────────────────────────────────────────────────────


@router.post("/run/{source_id}", response_model=None)
async def run_single(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Trigger a collector run for a single source."""
    service = CollectorService(db)
    try:
        result = await service.run_collector(source_id)
    except ValueError as exc:
        return {"success": False, "error": {"code": "NOT_FOUND", "message": str(exc)}}

    return success_response(data=asdict(result))


@router.post("/run-all", response_model=None)
async def run_all(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Trigger collector runs for all active sources."""
    service = CollectorService(db)
    results = await service.run_all_active()
    return success_response(data=results)


# ── Events ───────────────────────────────────────────────────────────────


@router.get("/events", response_model=None)
async def list_events(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    source: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List collected events with pagination and optional filters."""
    repo = EventRepository(db)
    events = await repo.list_events(
        limit=limit, offset=offset, source=source, event_type=event_type
    )
    total = await repo.count_events(source=source, event_type=event_type)
    return success_response(
        data={
            "events": [
                EventSummary.model_validate(e).model_dump() for e in events
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    )


# ── Source Health ────────────────────────────────────────────────────────


@router.get("/health", response_model=None)
async def source_health(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return per-source health status for monitoring."""
    repo = CollectorSourceRepository(db)
    sources = await repo.list_all()

    health_data: list[dict] = []
    for src in sources:
        # Compute status
        if not src.is_active:
            status = "inactive"
        elif src.consecutive_failures >= 5:
            status = "failing"
        elif src.consecutive_failures >= 2:
            status = "degraded"
        elif src.last_collected_at is not None:
            status = "healthy"
        else:
            status = "pending"

        h = CollectorSourceHealth.model_validate(src)
        h.status = status
        health_data.append(h.model_dump())

    return success_response(data=health_data)
