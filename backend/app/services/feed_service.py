"""Feed services — IntelligenceFeedService and TrendingService.

Business logic for search, feed generation, and trending aggregations.
Routers stay thin; all query orchestration lives here.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.repositories.feed_repository import FeedRepository
from app.schemas.feed import (
    CategoryCount,
    EntityCount,
    FeedDetail,
    FeedItem,
    FeedSearchResponse,
    PaginationMeta,
    TagCount,
    TrendingResponse,
    VALID_SORT_OPTIONS,
)

logger = get_logger("feed.service")


# ── Intelligence Feed Service ────────────────────────────────────────────


class IntelligenceFeedService:
    """Orchestrates search, feed generation, and query validation."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = FeedRepository(db)

    async def get_feed(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        sort: str = "newest",
    ) -> FeedSearchResponse:
        """Return the default intelligence feed (newest READY events)."""
        sort = self._validate_sort(sort)

        items = await self._repo.search(sort=sort, limit=limit, offset=offset)
        total = await self._repo.count_ready()

        return FeedSearchResponse(
            items=[FeedItem(**item) for item in items],
            pagination=PaginationMeta(
                limit=limit,
                offset=offset,
                total=total,
                has_more=(offset + limit) < total,
            ),
        )

    async def search(
        self,
        *,
        keyword: str | None = None,
        category: str | None = None,
        source: str | None = None,
        tag: str | None = None,
        importance_min: int | None = None,
        importance_max: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sort: str = "newest",
        limit: int = 50,
        offset: int = 0,
    ) -> FeedSearchResponse:
        """Search with combined filters, sorting, and pagination."""
        sort = self._validate_sort(sort)
        self._validate_importance_range(importance_min, importance_max)
        self._validate_date_range(date_from, date_to)

        filter_kwargs: dict[str, Any] = {}
        if keyword:
            filter_kwargs["keyword"] = keyword.strip()
        if category:
            filter_kwargs["category"] = category
        if source:
            filter_kwargs["source"] = source
        if tag:
            filter_kwargs["tag"] = tag
        if importance_min is not None:
            filter_kwargs["importance_min"] = importance_min
        if importance_max is not None:
            filter_kwargs["importance_max"] = importance_max
        if date_from:
            filter_kwargs["date_from"] = date_from
        if date_to:
            filter_kwargs["date_to"] = date_to

        items = await self._repo.search(
            **filter_kwargs, sort=sort, limit=limit, offset=offset
        )
        total = await self._repo.count_filtered(**filter_kwargs)

        return FeedSearchResponse(
            items=[FeedItem(**item) for item in items],
            pagination=PaginationMeta(
                limit=limit,
                offset=offset,
                total=total,
                has_more=(offset + limit) < total,
            ),
        )

    async def get_detail(self, event_id: uuid.UUID) -> FeedDetail | None:
        """Fetch a single feed item with full detail."""
        item = await self._repo.get_by_id(event_id)
        if item is None:
            return None
        return FeedDetail(**item)

    # ── Validation helpers ───────────────────────────────────────────────

    def _validate_sort(self, sort: str) -> str:
        """Validate and normalize sort parameter."""
        sort = sort.lower().strip()
        if sort not in VALID_SORT_OPTIONS:
            return "newest"
        return sort

    def _validate_importance_range(
        self, min_val: int | None, max_val: int | None
    ) -> None:
        """Validate importance score range."""
        if min_val is not None and max_val is not None and min_val > max_val:
            raise ValueError("importance_min cannot be greater than importance_max")

    def _validate_date_range(
        self, date_from: datetime | None, date_to: datetime | None
    ) -> None:
        """Validate date range."""
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from cannot be after date_to")


# ── Trending Service ─────────────────────────────────────────────────────


class TrendingService:
    """Deterministic trending intelligence from database aggregations."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = FeedRepository(db)

    async def get_trending(self, limit: int = 10) -> TrendingResponse:
        """Return aggregated trending data: top tags, categories, and stories."""
        top_tags_raw = await self._repo.top_tags(limit=limit)
        top_categories_raw = await self._repo.top_categories(limit=limit)
        most_important_raw = await self._repo.most_important(limit=limit)
        total_ready = await self._repo.count_ready()

        return TrendingResponse(
            top_tags=[TagCount(**t) for t in top_tags_raw],
            top_categories=[CategoryCount(**c) for c in top_categories_raw],
            most_important=[FeedItem(**item) for item in most_important_raw],
            total_ready=total_ready,
        )

    async def get_category_breakdown(self, limit: int = 20) -> list[CategoryCount]:
        """Return all categories with their event counts."""
        raw = await self._repo.top_categories(limit=limit)
        return [CategoryCount(**c) for c in raw]

    async def get_entity_breakdown(self, limit: int = 20) -> list[EntityCount]:
        """Return all entities with their occurrence counts."""
        raw = await self._repo.top_entities(limit=limit)
        return [EntityCount(**e) for e in raw]

    async def get_tag_cloud(self, limit: int = 30) -> list[TagCount]:
        """Return tag frequency counts for a tag cloud."""
        raw = await self._repo.top_tags(limit=limit)
        return [TagCount(**t) for t in raw]
