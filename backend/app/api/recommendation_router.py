"""Recommendation API router — personalized feed & preference endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.database.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas.recommendation import (
    PersonalizedFeedResponse,
    RecommendationExplanation,
    UserPreferenceRequest,
    UserPreferenceResponse,
)
from app.services.recommendation_service import (
    PreferenceService,
    RecommendationService,
)
from app.services.feed_service import TrendingService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# ── General Recommendations ──────────────────────────────────────────────


@router.get("", response_model=None)
async def get_recommendations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Non-personalized recommendations ranked by importance + freshness."""
    service = RecommendationService(db)
    result = await service.get_recommendations(limit=limit, offset=offset)
    return success_response(data=result.model_dump())


# ── Personalized For-You Feed ────────────────────────────────────────────


@router.get("/for-you", response_model=None)
async def get_for_you(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Personalized feed based on user preferences."""
    service = RecommendationService(db)
    result = await service.get_for_you(user, limit=limit, offset=offset)
    return success_response(data=result.model_dump())


# ── Trending Recommendations ─────────────────────────────────────────────


@router.get("/trending", response_model=None)
async def get_trending(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Trending recommendations reusing Sprint 5's TrendingService."""
    service = TrendingService(db)
    result = await service.get_trending(limit=limit)
    return success_response(data=result.model_dump())


# ── Explain Recommendation ───────────────────────────────────────────────


@router.get("/explain/{event_id}", response_model=None)
async def explain_recommendation(
    event_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Explain why an event scored as it did for a user."""
    service = RecommendationService(db)
    explanation = await service.explain(user, event_id)
    if explanation is None:
        return {
            "success": False,
            "error": {"code": "NOT_FOUND", "message": "Event not found."},
        }
    return success_response(data=explanation.model_dump())


# ── Preferences ──────────────────────────────────────────────────────────


@router.post("/preferences", response_model=None)
async def set_preferences(
    body: UserPreferenceRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Set or update user recommendation preferences."""
    service = PreferenceService(db)
    result = await service.update_preferences(
        user.id,
        preferred_categories=body.preferred_categories,
        preferred_sources=body.preferred_sources,
        muted_categories=body.muted_categories,
        muted_sources=body.muted_sources,
        preferred_technologies=body.preferred_technologies,
        preferred_organizations=body.preferred_organizations,
    )
    await db.commit()
    return success_response(
        data=result.model_dump(),
        message="Preferences updated successfully.",
    )


@router.get("/preferences", response_model=None)
async def get_preferences(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get current user recommendation preferences."""
    service = PreferenceService(db)
    result = await service.get_preferences(user.id)
    return success_response(data=result.model_dump())
