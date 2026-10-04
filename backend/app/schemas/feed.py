"""Pydantic schemas for the Search & Intelligence Feed."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.processed_event import AICategory, ProcessingStatus


# ── Pagination ───────────────────────────────────────────────────────────


class PaginationMeta(BaseModel):
    """Pagination metadata included in list responses."""

    limit: int
    offset: int
    total: int
    has_more: bool


# ── Feed Items ───────────────────────────────────────────────────────────


class FeedItem(BaseModel):
    """Lightweight feed item for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    collected_event_id: UUID
    cleaned_title: str
    ai_summary: str
    ai_category: AICategory
    ai_tags: list[str]
    importance_score: int
    source: str
    source_url: str
    organization: str
    published_at: datetime
    processed_at: datetime | None


class FeedDetail(BaseModel):
    """Full feed item with all enrichment data."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    collected_event_id: UUID
    cleaned_title: str
    cleaned_summary: str
    ai_summary: str
    ai_category: AICategory
    ai_tags: list[str]
    entities: dict[str, Any]
    importance_score: int
    importance_reason: str
    processing_status: ProcessingStatus
    source: str
    source_url: str
    organization: str
    published_at: datetime
    processed_at: datetime | None
    created_at: datetime

    # ── LLM Intelligence (Phase 2) ───────────────────────────────────────
    why_it_matters: str | None = None
    llm_summary: str | None = None
    intelligence_type: str | None = None
    llm_category: str | None = None
    confidence_score: float | None = None
    llm_keywords: list[str] | None = None
    llm_entities: dict[str, Any] | None = None
    llm_status: str | None = None


# ── Search ───────────────────────────────────────────────────────────────


VALID_SORT_OPTIONS = {"newest", "oldest", "highest_importance"}


class FeedSearchResponse(BaseModel):
    """Paginated search response."""

    items: list[FeedItem]
    pagination: PaginationMeta


# ── Trending ─────────────────────────────────────────────────────────────


class TagCount(BaseModel):
    """Tag with its occurrence count."""

    tag: str
    count: int


class CategoryCount(BaseModel):
    """Category with its event count."""

    category: str
    count: int


class EntityCount(BaseModel):
    """Entity with its occurrence count."""

    entity: str
    entity_type: str
    count: int


class TrendingResponse(BaseModel):
    """Aggregated trending intelligence data."""

    top_tags: list[TagCount]
    top_categories: list[CategoryCount]
    most_important: list[FeedItem]
    total_ready: int
