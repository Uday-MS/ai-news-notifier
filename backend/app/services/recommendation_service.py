"""Recommendation & Personalization services.

Contains:
- ScoringWeights: configurable scoring parameters
- ScoringEngine: stateless, independently testable scoring pipeline
- PreferenceService: user preference CRUD
- RecommendationService: personalized feed generation
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.user import User
from app.models.user_preference import UserPreference
from app.repositories.feed_repository import FeedRepository
from app.schemas.feed import FeedItem, PaginationMeta
from app.schemas.recommendation import (
    PersonalizedFeedResponse,
    RecommendationExplanation,
    RecommendationItem,
    ScoreFactor,
    UserPreferenceResponse,
)
from app.services.feed_service import TrendingService

logger = get_logger("recommendation.service")


# ── Scoring Weights ──────────────────────────────────────────────────────


@dataclass
class ScoringWeights:
    """Configurable weights for the recommendation scoring pipeline.

    All values are the maximum contribution of each factor.
    """

    preference_category: float = 30.0
    preference_source: float = 15.0
    importance_max: float = 25.0
    freshness_max: float = 20.0
    freshness_half_life_hours: float = 12.0
    trending_max: float = 10.0
    diversity_penalty: float = -15.0


# ── Scoring Engine ───────────────────────────────────────────────────────


class ScoringEngine:
    """Stateless deterministic scoring pipeline.

    Each stage produces a (score, reason) tuple. Stages:
    1. Preference Score — category/source affinity
    2. Importance Score — maps 0–100 to 0–max
    3. Freshness Score — exponential decay
    4. Trending Bonus — tag/category overlap with trending
    5. Diversity Penalty — penalizes consecutive same-category
    6. Mute Filter — excludes muted categories/sources
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        self.w = weights or ScoringWeights()

    def score_event(
        self,
        event: dict[str, Any],
        *,
        preferred_categories: list[str] | None = None,
        preferred_sources: list[str] | None = None,
        muted_categories: list[str] | None = None,
        muted_sources: list[str] | None = None,
        trending_tags: set[str] | None = None,
        trending_categories: set[str] | None = None,
        seen_categories: list[str] | None = None,
        now: datetime | None = None,
    ) -> tuple[float, list[ScoreFactor]]:
        """Score a single event and return (total, factors).

        Returns total = -1.0 if the event is muted.
        """
        factors: list[ScoreFactor] = []
        now = now or datetime.now(timezone.utc)

        # Stage 0: Mute filter
        if self._is_muted(event, muted_categories, muted_sources):
            return -1.0, [ScoreFactor(
                factor="muted", score=-1.0, reason="Event is in a muted category or source."
            )]

        # Stage 1: Preference score
        pref_score, pref_factors = self._preference_score(
            event, preferred_categories, preferred_sources
        )
        factors.extend(pref_factors)

        # Stage 2: Importance score
        imp_score, imp_factor = self._importance_score(event)
        factors.append(imp_factor)

        # Stage 3: Freshness score
        fresh_score, fresh_factor = self._freshness_score(event, now)
        factors.append(fresh_factor)

        # Stage 4: Trending bonus
        trend_score, trend_factor = self._trending_bonus(
            event, trending_tags, trending_categories
        )
        factors.append(trend_factor)

        # Stage 5: Diversity penalty
        div_score, div_factor = self._diversity_penalty(event, seen_categories)
        factors.append(div_factor)

        total = pref_score + imp_score + fresh_score + trend_score + div_score
        total = round(max(0.0, total), 2)

        return total, factors

    # ── Stage implementations ────────────────────────────────────────────

    def _is_muted(
        self,
        event: dict[str, Any],
        muted_categories: list[str] | None,
        muted_sources: list[str] | None,
    ) -> bool:
        """Check if event matches muted categories or sources."""
        category = self._get_category_str(event)
        source = event.get("source", "").lower()

        if muted_categories:
            if category in [c.lower() for c in muted_categories]:
                return True

        if muted_sources:
            if source in [s.lower() for s in muted_sources]:
                return True

        return False

    def _preference_score(
        self,
        event: dict[str, Any],
        preferred_categories: list[str] | None,
        preferred_sources: list[str] | None,
    ) -> tuple[float, list[ScoreFactor]]:
        """Score based on user's preferred categories and sources."""
        score = 0.0
        factors: list[ScoreFactor] = []
        category = self._get_category_str(event)
        source = event.get("source", "").lower()

        if preferred_categories:
            preferred_lower = [c.lower() for c in preferred_categories]
            if category in preferred_lower:
                score += self.w.preference_category
                factors.append(ScoreFactor(
                    factor="preferred_category",
                    score=self.w.preference_category,
                    reason=f"Category '{category}' is in your preferred list.",
                ))

        if preferred_sources:
            preferred_lower = [s.lower() for s in preferred_sources]
            if source in preferred_lower:
                score += self.w.preference_source
                factors.append(ScoreFactor(
                    factor="preferred_source",
                    score=self.w.preference_source,
                    reason=f"Source '{source}' is in your preferred list.",
                ))

        if not factors:
            factors.append(ScoreFactor(
                factor="preference", score=0.0, reason="No preference match."
            ))

        return score, factors

    def _importance_score(self, event: dict[str, Any]) -> tuple[float, ScoreFactor]:
        """Map the 0–100 importance_score to 0–max range."""
        raw = event.get("importance_score", 0)
        score = (raw / 100.0) * self.w.importance_max
        score = round(score, 2)
        return score, ScoreFactor(
            factor="importance",
            score=score,
            reason=f"Importance score {raw}/100 → {score:.1f} points.",
        )

    def _freshness_score(
        self, event: dict[str, Any], now: datetime
    ) -> tuple[float, ScoreFactor]:
        """Exponential decay: full score if recent, halved per half-life."""
        published = event.get("published_at")
        if not published:
            return 0.0, ScoreFactor(
                factor="freshness", score=0.0, reason="No publish date available."
            )

        if isinstance(published, str):
            published = datetime.fromisoformat(published)

        # Ensure timezone-aware comparison
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)

        hours_old = max(0.0, (now - published).total_seconds() / 3600.0)
        decay = math.exp(-0.693 * hours_old / self.w.freshness_half_life_hours)
        score = round(self.w.freshness_max * decay, 2)

        if hours_old < 6:
            label = "Very fresh"
        elif hours_old < 24:
            label = "Recent"
        elif hours_old < 72:
            label = f"{int(hours_old / 24)}d old"
        else:
            label = f"{int(hours_old / 24)}d old"

        return score, ScoreFactor(
            factor="freshness",
            score=score,
            reason=f"{label} ({hours_old:.0f}h) → {score:.1f} points.",
        )

    def _trending_bonus(
        self,
        event: dict[str, Any],
        trending_tags: set[str] | None,
        trending_categories: set[str] | None,
    ) -> tuple[float, ScoreFactor]:
        """Boost events whose tags/category overlap with trending data."""
        if not trending_tags and not trending_categories:
            return 0.0, ScoreFactor(
                factor="trending", score=0.0, reason="No trending data available."
            )

        score = 0.0
        reasons: list[str] = []
        category = self._get_category_str(event)

        if trending_categories and category in trending_categories:
            score += self.w.trending_max * 0.5
            reasons.append(f"Category '{category}' is trending.")

        if trending_tags:
            event_tags = set(t.lower() for t in event.get("ai_tags", []))
            overlap = event_tags & trending_tags
            if overlap:
                tag_bonus = min(
                    self.w.trending_max * 0.5,
                    len(overlap) * (self.w.trending_max * 0.5 / 3),
                )
                score += tag_bonus
                reasons.append(f"Tags {overlap} are trending.")

        score = round(min(score, self.w.trending_max), 2)
        reason = " ".join(reasons) if reasons else "No trending overlap."

        return score, ScoreFactor(factor="trending", score=score, reason=reason)

    def _diversity_penalty(
        self, event: dict[str, Any], seen_categories: list[str] | None
    ) -> tuple[float, ScoreFactor]:
        """Penalize if the same category appeared recently in the list."""
        if not seen_categories:
            return 0.0, ScoreFactor(
                factor="diversity", score=0.0, reason="First event, no penalty."
            )

        category = self._get_category_str(event)
        count = sum(1 for c in seen_categories if c == category)

        if count == 0:
            return 0.0, ScoreFactor(
                factor="diversity", score=0.0, reason="New category, no penalty."
            )

        penalty = self.w.diversity_penalty * min(count / 3.0, 1.0)
        penalty = round(penalty, 2)

        return penalty, ScoreFactor(
            factor="diversity",
            score=penalty,
            reason=f"Category '{category}' seen {count}x → {penalty:.1f} penalty.",
        )

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _get_category_str(event: dict[str, Any]) -> str:
        """Extract category as a lowercase string."""
        cat = event.get("ai_category", "other")
        return cat.value if hasattr(cat, "value") else str(cat).lower()


# ── Preference Service ───────────────────────────────────────────────────


class PreferenceService:
    """CRUD for user recommendation preferences."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_preferences(self, user_id: uuid.UUID) -> UserPreferenceResponse:
        """Return current preferences or defaults."""
        pref = await self._get_or_none(user_id)
        if pref is None:
            return UserPreferenceResponse(
                user_id=user_id,
                preferred_categories=[],
                preferred_sources=[],
                muted_categories=[],
                muted_sources=[],
            )
        return UserPreferenceResponse.model_validate(pref)

    async def update_preferences(
        self,
        user_id: uuid.UUID,
        *,
        preferred_categories: list[str] | None = None,
        preferred_sources: list[str] | None = None,
        muted_categories: list[str] | None = None,
        muted_sources: list[str] | None = None,
    ) -> UserPreferenceResponse:
        """Upsert user preferences."""
        pref = await self._get_or_none(user_id)

        if pref is None:
            pref = UserPreference(
                user_id=user_id,
                preferred_categories=preferred_categories or [],
                preferred_sources=preferred_sources or [],
                muted_categories=muted_categories or [],
                muted_sources=muted_sources or [],
            )
            self._db.add(pref)
        else:
            if preferred_categories is not None:
                pref.preferred_categories = preferred_categories
            if preferred_sources is not None:
                pref.preferred_sources = preferred_sources
            if muted_categories is not None:
                pref.muted_categories = muted_categories
            if muted_sources is not None:
                pref.muted_sources = muted_sources

        await self._db.flush()
        await self._db.refresh(pref)
        return UserPreferenceResponse.model_validate(pref)

    async def _get_or_none(self, user_id: uuid.UUID) -> UserPreference | None:
        result = await self._db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()


# ── Recommendation Service ───────────────────────────────────────────────


class RecommendationService:
    """Generates personalized and general recommendation feeds.

    Injects FeedRepository (Sprint 5) for candidate selection and
    TrendingService for trending data. No duplicate SQL.
    """

    def __init__(
        self,
        db: AsyncSession,
        scoring_weights: ScoringWeights | None = None,
    ) -> None:
        self._db = db
        self._feed_repo = FeedRepository(db)
        self._pref_service = PreferenceService(db)
        self._trending_service = TrendingService(db)
        self._engine = ScoringEngine(scoring_weights)

    async def get_for_you(
        self,
        user: User,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> PersonalizedFeedResponse:
        """Generate a personalized feed for an authenticated user."""
        prefs = await self._pref_service.get_preferences(user.id)

        # Fetch a larger candidate pool for scoring + diversity
        pool_size = max(limit * 3, 60)
        candidates = await self._feed_repo.search(limit=pool_size, offset=0)
        total_ready = await self._feed_repo.count_ready()

        # Get trending data for bonus scoring
        trending_tags, trending_categories = await self._get_trending_sets()

        # Score and rank
        scored = self._score_candidates(
            candidates,
            preferred_categories=prefs.preferred_categories,
            preferred_sources=prefs.preferred_sources,
            muted_categories=prefs.muted_categories,
            muted_sources=prefs.muted_sources,
            trending_tags=trending_tags,
            trending_categories=trending_categories,
        )

        # Paginate
        page = scored[offset: offset + limit]

        return PersonalizedFeedResponse(
            items=page,
            pagination=PaginationMeta(
                limit=limit,
                offset=offset,
                total=len(scored),
                has_more=(offset + limit) < len(scored),
            ),
        )

    async def get_recommendations(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> PersonalizedFeedResponse:
        """Non-personalized recommendations using importance + freshness."""
        pool_size = max(limit * 3, 60)
        candidates = await self._feed_repo.search(limit=pool_size, offset=0)
        total_ready = await self._feed_repo.count_ready()

        trending_tags, trending_categories = await self._get_trending_sets()

        scored = self._score_candidates(
            candidates,
            trending_tags=trending_tags,
            trending_categories=trending_categories,
        )

        page = scored[offset: offset + limit]

        return PersonalizedFeedResponse(
            items=page,
            pagination=PaginationMeta(
                limit=limit,
                offset=offset,
                total=len(scored),
                has_more=(offset + limit) < len(scored),
            ),
        )

    async def explain(
        self,
        user: User,
        event_id: uuid.UUID,
    ) -> RecommendationExplanation | None:
        """Return a detailed scoring breakdown for a single event."""
        event_data = await self._feed_repo.get_by_id(event_id)
        if event_data is None:
            return None

        prefs = await self._pref_service.get_preferences(user.id)
        trending_tags, trending_categories = await self._get_trending_sets()

        total, factors = self._engine.score_event(
            event_data,
            preferred_categories=prefs.preferred_categories,
            preferred_sources=prefs.preferred_sources,
            muted_categories=prefs.muted_categories,
            muted_sources=prefs.muted_sources,
            trending_tags=trending_tags,
            trending_categories=trending_categories,
        )

        return RecommendationExplanation(
            event_id=event_id,
            cleaned_title=event_data["cleaned_title"],
            total_score=total,
            factors=factors,
        )

    # ── Internal helpers ─────────────────────────────────────────────────

    def _score_candidates(
        self,
        candidates: list[dict[str, Any]],
        *,
        preferred_categories: list[str] | None = None,
        preferred_sources: list[str] | None = None,
        muted_categories: list[str] | None = None,
        muted_sources: list[str] | None = None,
        trending_tags: set[str] | None = None,
        trending_categories: set[str] | None = None,
    ) -> list[RecommendationItem]:
        """Score, filter muted, apply diversity, sort by score."""
        now = datetime.now(timezone.utc)
        scored: list[tuple[float, dict, list[ScoreFactor]]] = []
        seen_categories: list[str] = []

        # First pass: score without diversity
        pre_scored: list[tuple[float, dict, list[ScoreFactor]]] = []
        for candidate in candidates:
            total, factors = self._engine.score_event(
                candidate,
                preferred_categories=preferred_categories,
                preferred_sources=preferred_sources,
                muted_categories=muted_categories,
                muted_sources=muted_sources,
                trending_tags=trending_tags,
                trending_categories=trending_categories,
                now=now,
            )
            if total >= 0:  # Exclude muted (score == -1)
                pre_scored.append((total, candidate, factors))

        # Sort by score descending
        pre_scored.sort(key=lambda x: x[0], reverse=True)

        # Second pass: apply diversity penalty in ranked order
        results: list[RecommendationItem] = []
        seen: list[str] = []

        for base_score, candidate, factors in pre_scored:
            category = self._engine._get_category_str(candidate)
            div_score, div_factor = self._engine._diversity_penalty(candidate, seen)

            final_score = round(max(0.0, base_score + div_score), 2)

            # Replace the diversity factor with the real one
            final_factors = [f for f in factors if f.factor != "diversity"]
            final_factors.append(div_factor)

            reasons = [
                f.reason for f in final_factors
                if f.score != 0.0 and f.factor != "muted"
            ]

            results.append(RecommendationItem(
                # FeedItem fields
                id=candidate["id"],
                collected_event_id=candidate["collected_event_id"],
                cleaned_title=candidate["cleaned_title"],
                ai_summary=candidate["ai_summary"],
                ai_category=candidate["ai_category"],
                ai_tags=candidate["ai_tags"],
                importance_score=candidate["importance_score"],
                source=candidate["source"],
                source_url=candidate["source_url"],
                organization=candidate["organization"],
                published_at=candidate["published_at"],
                processed_at=candidate["processed_at"],
                # Recommendation fields
                recommendation_score=final_score,
                recommendation_reasons=reasons,
            ))

            seen.append(category)

        # Re-sort after diversity adjustment
        results.sort(key=lambda x: x.recommendation_score, reverse=True)

        return results

    async def _get_trending_sets(self) -> tuple[set[str], set[str]]:
        """Fetch trending tags and categories as sets for fast lookup."""
        try:
            trending = await self._trending_service.get_trending(limit=10)
            tags = {t.tag.lower() for t in trending.top_tags}
            categories = {c.category.lower() for c in trending.top_categories}
            return tags, categories
        except Exception:
            return set(), set()
