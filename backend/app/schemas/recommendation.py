"""Pydantic schemas for the Recommendation & Personalization Engine."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.processed_event import AICategory
from app.schemas.feed import FeedItem, PaginationMeta


# ── User Preferences ────────────────────────────────────────────────────


class UserPreferenceRequest(BaseModel):
    """Input for setting/updating user preferences."""

    preferred_categories: list[str] = Field(default_factory=list)
    preferred_sources: list[str] = Field(default_factory=list)
    muted_categories: list[str] = Field(default_factory=list)
    muted_sources: list[str] = Field(default_factory=list)
    preferred_technologies: list[str] = Field(default_factory=list)
    preferred_organizations: list[str] = Field(default_factory=list)


class UserPreferenceResponse(BaseModel):
    """Output with current user preferences."""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    preferred_categories: list[str]
    preferred_sources: list[str]
    muted_categories: list[str]
    muted_sources: list[str]
    preferred_technologies: list[str] = Field(default_factory=list)
    preferred_organizations: list[str] = Field(default_factory=list)


# ── Recommendation Items ────────────────────────────────────────────────


class RecommendationItem(FeedItem):
    """Feed item extended with recommendation scoring."""

    recommendation_score: float
    recommendation_reasons: list[str]
    why_it_matters: str | None = None
    llm_summary: str | None = None
    intelligence_type: str | None = None
    confidence_score: float | None = None


class PersonalizedFeedResponse(BaseModel):
    """Paginated personalized feed response."""

    items: list[RecommendationItem]
    pagination: PaginationMeta


# ── Explanation ─────────────────────────────────────────────────────────


class ScoreFactor(BaseModel):
    """A single scoring factor in the explanation."""

    factor: str
    score: float
    reason: str


class RecommendationExplanation(BaseModel):
    """Detailed breakdown of why an event scored as it did."""

    event_id: UUID
    cleaned_title: str
    total_score: float
    factors: list[ScoreFactor]
