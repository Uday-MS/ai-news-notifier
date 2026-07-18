"""Feed API router — Intelligence Feed & Search endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.database.session import get_db
from app.schemas.feed import (
    CategoryCount,
    EntityCount,
    FeedDetail,
    FeedSearchResponse,
    TagCount,
    TrendingResponse,
)
from app.services.feed_service import IntelligenceFeedService, TrendingService

router = APIRouter(prefix="/feed", tags=["feed"])


# ── Default Feed ─────────────────────────────────────────────────────────


@router.get("", response_model=None)
async def get_feed(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="newest"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return the default intelligence feed of READY processed events."""
    service = IntelligenceFeedService(db)
    result = await service.get_feed(limit=limit, offset=offset, sort=sort)
    return success_response(data=result.model_dump())


# ── Search ───────────────────────────────────────────────────────────────


@router.get("/search", response_model=None)
async def search_feed(
    q: str | None = Query(default=None, description="Keyword search"),
    category: str | None = Query(default=None),
    source: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    importance_min: int | None = Query(default=None, ge=0, le=100),
    importance_max: int | None = Query(default=None, ge=0, le=100),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    sort: str = Query(default="newest"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Search processed events with keyword, filters, and sorting."""
    service = IntelligenceFeedService(db)
    try:
        result = await service.search(
            keyword=q,
            category=category,
            source=source,
            tag=tag,
            importance_min=importance_min,
            importance_max=importance_max,
            date_from=date_from,
            date_to=date_to,
            sort=sort,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        return {
            "success": False,
            "error": {"code": "VALIDATION_ERROR", "message": str(exc)},
        }
    return success_response(data=result.model_dump())


# ── Trending ─────────────────────────────────────────────────────────────


@router.get("/trending", response_model=None)
async def get_trending(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return trending intelligence: top tags, categories, and stories."""
    service = TrendingService(db)
    result = await service.get_trending(limit=limit)
    return success_response(data=result.model_dump())


# ── Categories ───────────────────────────────────────────────────────────


@router.get("/categories", response_model=None)
async def get_categories(
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return category breakdown with event counts."""
    service = TrendingService(db)
    categories = await service.get_category_breakdown(limit=limit)
    return success_response(data=[c.model_dump() for c in categories])


# ── Entities ─────────────────────────────────────────────────────────────


@router.get("/entities", response_model=None)
async def get_entities(
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return entity breakdown with occurrence counts."""
    service = TrendingService(db)
    entities = await service.get_entity_breakdown(limit=limit)
    return success_response(data=[e.model_dump() for e in entities])


# ── Tags ─────────────────────────────────────────────────────────────────


@router.get("/tags", response_model=None)
async def get_tags(
    limit: int = Query(default=30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return tag cloud with frequency counts."""
    service = TrendingService(db)
    tags = await service.get_tag_cloud(limit=limit)
    return success_response(data=[t.model_dump() for t in tags])


# ── Detail ───────────────────────────────────────────────────────────────


@router.get("/{event_id}", response_model=None)
async def get_feed_detail(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return a single feed item with full enrichment data."""
    service = IntelligenceFeedService(db)
    detail = await service.get_detail(event_id)
    if detail is None:
        return {
            "success": False,
            "error": {"code": "NOT_FOUND", "message": "Feed item not found."},
        }
    return success_response(data=detail.model_dump())
