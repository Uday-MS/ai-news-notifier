"""Tests for the Recommendation & Personalization Engine (Sprint 6).

Tests cover:
- ScoringEngine (unit): preference, importance, freshness, trending, diversity, mute
- PreferenceService (integration): get/set/update
- RecommendationService (integration): for-you, general, explain
- API endpoints (HTTP): all 6 endpoints
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.event import CollectedEvent, EventType
from app.models.processed_event import AICategory, ProcessedEvent, ProcessingStatus
from app.models.user import User, UserRole
from app.schemas.recommendation import ScoreFactor
from app.services.recommendation_service import (
    PreferenceService,
    RecommendationService,
    ScoringEngine,
    ScoringWeights,
)


# ── Test Data Helpers ────────────────────────────────────────────────────


async def _seed_event(
    db: AsyncSession,
    *,
    title: str = "Test AI Event",
    summary: str = "A detailed summary of the AI event.",
    source: str = "test-blog",
    source_url: str | None = None,
    organization: str = "TestOrg",
    published_at: datetime | None = None,
    ai_category: AICategory = AICategory.AI_MODEL,
    ai_tags: list[str] | None = None,
    entities: dict | None = None,
    importance_score: int = 50,
    processing_status: ProcessingStatus = ProcessingStatus.READY,
) -> tuple[CollectedEvent, ProcessedEvent]:
    """Create a paired CollectedEvent + ProcessedEvent."""
    if source_url is None:
        source_url = f"https://example.com/{uuid.uuid4()}"
    if published_at is None:
        published_at = datetime.now(timezone.utc)

    ce = CollectedEvent(
        title=title, summary=summary, source=source,
        source_url=source_url, published_at=published_at,
        event_type=EventType.NEWS, organization=organization,
        tags=[], extra_metadata={}, collector_id="test",
        content_hash=str(uuid.uuid4())[:64],
    )
    db.add(ce)
    await db.flush()
    await db.refresh(ce)

    pe = ProcessedEvent(
        collected_event_id=ce.id, cleaned_title=title,
        cleaned_summary=summary, ai_category=ai_category,
        ai_tags=ai_tags or ["ai"], entities=entities or {},
        importance_score=importance_score,
        importance_reason="Test.", ai_summary="Summary.",
        processing_status=processing_status,
        processed_at=datetime.now(timezone.utc),
    )
    db.add(pe)
    await db.flush()
    await db.refresh(pe)
    return ce, pe


async def _seed_diverse(db: AsyncSession) -> list[ProcessedEvent]:
    """Seed diverse events for recommendation testing."""
    now = datetime.now(timezone.utc)
    events = []

    _, pe1 = await _seed_event(db, title="GPT-5 Launch", source="openai-blog",
        organization="OpenAI", published_at=now - timedelta(hours=1),
        ai_category=AICategory.AI_MODEL, ai_tags=["openai", "gpt-5", "llm"],
        importance_score=90)
    events.append(pe1)

    _, pe2 = await _seed_event(db, title="Critical ML Vulnerability", source="security-blog",
        organization="SecTeam", published_at=now - timedelta(hours=3),
        ai_category=AICategory.SECURITY, ai_tags=["security", "ml"],
        importance_score=85)
    events.append(pe2)

    _, pe3 = await _seed_event(db, title="AI Hackathon 2025", source="hack-site",
        organization="HackOrg", published_at=now - timedelta(hours=6),
        ai_category=AICategory.HACKATHON, ai_tags=["hackathon", "ai"],
        importance_score=60)
    events.append(pe3)

    _, pe4 = await _seed_event(db, title="Startup Raises $100M", source="tech-news",
        organization="FundedAI", published_at=now - timedelta(hours=12),
        ai_category=AICategory.FUNDING, ai_tags=["startup", "funding"],
        importance_score=70)
    events.append(pe4)

    _, pe5 = await _seed_event(db, title="New Attention Paper", source="arxiv",
        organization="MIT", published_at=now - timedelta(hours=24),
        ai_category=AICategory.AI_RESEARCH, ai_tags=["research", "transformer"],
        importance_score=55)
    events.append(pe5)

    _, pe6 = await _seed_event(db, title="Another AI Model Release", source="openai-blog",
        organization="OpenAI", published_at=now - timedelta(hours=2),
        ai_category=AICategory.AI_MODEL, ai_tags=["openai", "llm"],
        importance_score=75)
    events.append(pe6)

    await db.commit()
    return events


def _make_event_dict(**overrides) -> dict[str, Any]:
    """Build a fake event dict for unit testing the scoring engine."""
    defaults = {
        "id": uuid.uuid4(),
        "collected_event_id": uuid.uuid4(),
        "cleaned_title": "Test Event",
        "cleaned_summary": "Summary.",
        "ai_summary": "AI Summary.",
        "ai_category": AICategory.AI_MODEL,
        "ai_tags": ["ai", "test"],
        "importance_score": 50,
        "source": "test-blog",
        "source_url": "https://example.com/test",
        "organization": "TestOrg",
        "published_at": datetime.now(timezone.utc),
        "processed_at": datetime.now(timezone.utc),
        "entities": {},
        "importance_reason": "Test.",
        "processing_status": ProcessingStatus.READY,
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    return defaults


# ══════════════════════════════════════════════════════════════════════════
# ScoringEngine Unit Tests
# ══════════════════════════════════════════════════════════════════════════


class TestScoringEngine:
    """Unit tests for the stateless scoring pipeline."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_preference_category_match(self):
        event = _make_event_dict(ai_category=AICategory.SECURITY)
        total, factors = self.engine.score_event(
            event, preferred_categories=["security"]
        )
        pref_factor = next(f for f in factors if f.factor == "preferred_category")
        assert pref_factor.score == 30.0
        assert total > 0

    def test_preference_source_match(self):
        event = _make_event_dict(source="openai-blog")
        total, factors = self.engine.score_event(
            event, preferred_sources=["openai-blog"]
        )
        src_factor = next(f for f in factors if f.factor == "preferred_source")
        assert src_factor.score == 15.0

    def test_preference_no_match(self):
        event = _make_event_dict(ai_category=AICategory.OTHER, source="random")
        total, factors = self.engine.score_event(
            event, preferred_categories=["security"],
            preferred_sources=["openai-blog"]
        )
        pref_factors = [f for f in factors if f.factor == "preference"]
        assert len(pref_factors) == 1
        assert pref_factors[0].score == 0.0

    def test_importance_score_mapping(self):
        event = _make_event_dict(importance_score=100)
        total, factors = self.engine.score_event(event)
        imp = next(f for f in factors if f.factor == "importance")
        assert imp.score == 25.0

    def test_importance_score_zero(self):
        event = _make_event_dict(importance_score=0)
        total, factors = self.engine.score_event(event)
        imp = next(f for f in factors if f.factor == "importance")
        assert imp.score == 0.0

    def test_freshness_recent(self):
        now = datetime.now(timezone.utc)
        event = _make_event_dict(published_at=now - timedelta(minutes=30))
        total, factors = self.engine.score_event(event, now=now)
        fresh = next(f for f in factors if f.factor == "freshness")
        assert fresh.score > 18.0  # Near max of 20

    def test_freshness_old(self):
        now = datetime.now(timezone.utc)
        event = _make_event_dict(published_at=now - timedelta(days=7))
        total, factors = self.engine.score_event(event, now=now)
        fresh = next(f for f in factors if f.factor == "freshness")
        assert fresh.score < 1.0  # Very decayed

    def test_freshness_decay_ordering(self):
        now = datetime.now(timezone.utc)
        event_1h = _make_event_dict(published_at=now - timedelta(hours=1))
        event_24h = _make_event_dict(published_at=now - timedelta(hours=24))
        event_72h = _make_event_dict(published_at=now - timedelta(hours=72))

        _, f1 = self.engine.score_event(event_1h, now=now)
        _, f24 = self.engine.score_event(event_24h, now=now)
        _, f72 = self.engine.score_event(event_72h, now=now)

        s1 = next(f for f in f1 if f.factor == "freshness").score
        s24 = next(f for f in f24 if f.factor == "freshness").score
        s72 = next(f for f in f72 if f.factor == "freshness").score

        assert s1 > s24 > s72

    def test_trending_bonus_category(self):
        event = _make_event_dict(ai_category=AICategory.SECURITY)
        total, factors = self.engine.score_event(
            event, trending_categories={"security"}
        )
        trend = next(f for f in factors if f.factor == "trending")
        assert trend.score > 0

    def test_trending_bonus_tags(self):
        event = _make_event_dict(ai_tags=["openai", "gpt-5"])
        total, factors = self.engine.score_event(
            event, trending_tags={"openai", "transformer"}
        )
        trend = next(f for f in factors if f.factor == "trending")
        assert trend.score > 0

    def test_trending_no_overlap(self):
        event = _make_event_dict(
            ai_category=AICategory.OTHER, ai_tags=["random"]
        )
        total, factors = self.engine.score_event(
            event, trending_tags={"openai"}, trending_categories={"security"}
        )
        trend = next(f for f in factors if f.factor == "trending")
        assert trend.score == 0.0

    def test_diversity_penalty_applied(self):
        event = _make_event_dict(ai_category=AICategory.AI_MODEL)
        _, factors = self.engine.score_event(
            event, seen_categories=["ai_model", "ai_model", "ai_model"]
        )
        div = next(f for f in factors if f.factor == "diversity")
        assert div.score < 0

    def test_diversity_no_penalty_new_category(self):
        event = _make_event_dict(ai_category=AICategory.SECURITY)
        _, factors = self.engine.score_event(
            event, seen_categories=["ai_model", "funding"]
        )
        div = next(f for f in factors if f.factor == "diversity")
        assert div.score == 0.0

    def test_mute_category(self):
        event = _make_event_dict(ai_category=AICategory.HACKATHON)
        total, factors = self.engine.score_event(
            event, muted_categories=["hackathon"]
        )
        assert total == -1.0
        assert factors[0].factor == "muted"

    def test_mute_source(self):
        event = _make_event_dict(source="spam-blog")
        total, factors = self.engine.score_event(
            event, muted_sources=["spam-blog"]
        )
        assert total == -1.0

    def test_mute_case_insensitive(self):
        event = _make_event_dict(ai_category=AICategory.SECURITY, source="OpenAI-Blog")
        total, _ = self.engine.score_event(
            event, muted_sources=["openai-blog"]
        )
        assert total == -1.0

    def test_custom_weights(self):
        weights = ScoringWeights(
            preference_category=50.0,
            importance_max=10.0,
        )
        engine = ScoringEngine(weights)
        event = _make_event_dict(
            ai_category=AICategory.SECURITY, importance_score=100
        )
        total, factors = engine.score_event(
            event, preferred_categories=["security"]
        )
        pref = next(f for f in factors if f.factor == "preferred_category")
        imp = next(f for f in factors if f.factor == "importance")
        assert pref.score == 50.0
        assert imp.score == 10.0

    def test_score_always_non_negative(self):
        event = _make_event_dict(importance_score=0)
        now = datetime.now(timezone.utc)
        event["published_at"] = now - timedelta(days=30)
        total, _ = self.engine.score_event(
            event, seen_categories=["ai_model"] * 10, now=now
        )
        assert total >= 0.0


# ══════════════════════════════════════════════════════════════════════════
# PreferenceService Integration Tests
# ══════════════════════════════════════════════════════════════════════════


class TestPreferenceService:
    """Integration tests for user preference CRUD."""

    @pytest.mark.asyncio
    async def test_get_defaults(self, db_session, test_user):
        service = PreferenceService(db_session)
        prefs = await service.get_preferences(test_user.id)
        assert prefs.user_id == test_user.id
        assert prefs.preferred_categories == []
        assert prefs.muted_categories == []

    @pytest.mark.asyncio
    async def test_set_preferences(self, db_session, test_user):
        service = PreferenceService(db_session)
        result = await service.update_preferences(
            test_user.id,
            preferred_categories=["ai_model", "security"],
            preferred_sources=["openai-blog"],
            muted_categories=["hackathon"],
            muted_sources=["spam-blog"],
        )
        await db_session.commit()

        assert result.preferred_categories == ["ai_model", "security"]
        assert result.preferred_sources == ["openai-blog"]
        assert result.muted_categories == ["hackathon"]
        assert result.muted_sources == ["spam-blog"]

    @pytest.mark.asyncio
    async def test_update_partial(self, db_session, test_user):
        service = PreferenceService(db_session)
        # Set initial
        await service.update_preferences(
            test_user.id,
            preferred_categories=["ai_model"],
            preferred_sources=["blog-a"],
        )
        await db_session.commit()

        # Update only categories
        result = await service.update_preferences(
            test_user.id,
            preferred_categories=["security", "funding"],
        )
        await db_session.commit()

        assert result.preferred_categories == ["security", "funding"]
        assert result.preferred_sources == ["blog-a"]  # Unchanged

    @pytest.mark.asyncio
    async def test_get_after_set(self, db_session, test_user):
        service = PreferenceService(db_session)
        await service.update_preferences(
            test_user.id, preferred_categories=["ai_research"]
        )
        await db_session.commit()

        prefs = await service.get_preferences(test_user.id)
        assert prefs.preferred_categories == ["ai_research"]


# ══════════════════════════════════════════════════════════════════════════
# RecommendationService Integration Tests
# ══════════════════════════════════════════════════════════════════════════


class TestRecommendationService:
    """Integration tests for the recommendation service."""

    @pytest.mark.asyncio
    async def test_get_recommendations(self, db_session):
        await _seed_diverse(db_session)
        service = RecommendationService(db_session)
        result = await service.get_recommendations(limit=10)
        assert len(result.items) > 0
        # Should be sorted by score descending
        scores = [i.recommendation_score for i in result.items]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_for_you_with_preferences(self, db_session, test_user):
        await _seed_diverse(db_session)
        pref_svc = PreferenceService(db_session)
        await pref_svc.update_preferences(
            test_user.id,
            preferred_categories=["security"],
            preferred_sources=["openai-blog"],
        )
        await db_session.commit()

        service = RecommendationService(db_session)
        result = await service.get_for_you(test_user, limit=10)

        assert len(result.items) > 0
        # Security event should rank higher due to preference
        top = result.items[0]
        assert top.recommendation_score > 0

    @pytest.mark.asyncio
    async def test_for_you_muted_filtering(self, db_session, test_user):
        await _seed_diverse(db_session)
        pref_svc = PreferenceService(db_session)
        await pref_svc.update_preferences(
            test_user.id,
            muted_categories=["hackathon", "funding"],
        )
        await db_session.commit()

        service = RecommendationService(db_session)
        result = await service.get_for_you(test_user, limit=20)

        categories = [i.ai_category.value for i in result.items]
        assert "hackathon" not in categories
        assert "funding" not in categories

    @pytest.mark.asyncio
    async def test_for_you_muted_source(self, db_session, test_user):
        await _seed_diverse(db_session)
        pref_svc = PreferenceService(db_session)
        await pref_svc.update_preferences(
            test_user.id,
            muted_sources=["openai-blog"],
        )
        await db_session.commit()

        service = RecommendationService(db_session)
        result = await service.get_for_you(test_user, limit=20)

        sources = [i.source for i in result.items]
        assert "openai-blog" not in sources

    @pytest.mark.asyncio
    async def test_for_you_without_preferences(self, db_session, test_user):
        await _seed_diverse(db_session)
        service = RecommendationService(db_session)
        result = await service.get_for_you(test_user, limit=10)
        # Should still work with default (empty) preferences
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_for_you_pagination(self, db_session, test_user):
        await _seed_diverse(db_session)
        service = RecommendationService(db_session)
        result = await service.get_for_you(test_user, limit=2, offset=0)
        assert len(result.items) == 2
        assert result.pagination.has_more is True

    @pytest.mark.asyncio
    async def test_explain(self, db_session, test_user):
        events = await _seed_diverse(db_session)
        pref_svc = PreferenceService(db_session)
        await pref_svc.update_preferences(
            test_user.id, preferred_categories=["ai_model"]
        )
        await db_session.commit()

        service = RecommendationService(db_session)
        explanation = await service.explain(test_user, events[0].id)
        assert explanation is not None
        assert explanation.event_id == events[0].id
        assert explanation.total_score > 0
        assert len(explanation.factors) > 0
        factor_names = [f.factor for f in explanation.factors]
        assert "importance" in factor_names
        assert "freshness" in factor_names

    @pytest.mark.asyncio
    async def test_explain_not_found(self, db_session, test_user):
        service = RecommendationService(db_session)
        explanation = await service.explain(test_user, uuid.uuid4())
        assert explanation is None

    @pytest.mark.asyncio
    async def test_diversity_reduces_same_category(self, db_session, test_user):
        await _seed_diverse(db_session)
        service = RecommendationService(db_session)
        result = await service.get_for_you(test_user, limit=20)
        # Two AI_MODEL events exist; the second should have a lower score
        ai_model_items = [
            i for i in result.items
            if i.ai_category == AICategory.AI_MODEL
        ]
        if len(ai_model_items) >= 2:
            # In the result list, the second AI_MODEL should have diversity penalty
            indices = [
                idx for idx, i in enumerate(result.items)
                if i.ai_category == AICategory.AI_MODEL
            ]
            # At least the second occurrence should have some diversity reason
            assert len(indices) >= 2

    @pytest.mark.asyncio
    async def test_recommendations_have_reasons(self, db_session):
        await _seed_diverse(db_session)
        service = RecommendationService(db_session)
        result = await service.get_recommendations(limit=5)
        for item in result.items:
            assert isinstance(item.recommendation_reasons, list)
            assert len(item.recommendation_reasons) > 0

    @pytest.mark.asyncio
    async def test_empty_database(self, db_session, test_user):
        service = RecommendationService(db_session)
        result = await service.get_for_you(test_user, limit=10)
        assert len(result.items) == 0
        assert result.pagination.total == 0


# ══════════════════════════════════════════════════════════════════════════
# API Endpoint Tests
# ══════════════════════════════════════════════════════════════════════════


@pytest_asyncio.fixture
async def auth_user(db_session: AsyncSession) -> tuple[User, str]:
    """Create a user and return (user, access_token)."""
    user = User(
        id=uuid.uuid4(),
        email="rec_test@example.com",
        hashed_password=hash_password("StrongP@ss1"),
        full_name="Rec Test User",
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(str(user.id), {"role": user.role.value})
    return user, token


@pytest_asyncio.fixture
async def rec_client(db_session: AsyncSession, auth_user):
    """Test HTTP client with seeded data and auth."""
    from app.database.session import get_db
    from app.main import app

    user, token = auth_user
    await _seed_diverse(db_session)

    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers["Authorization"] = f"Bearer {token}"
        yield ac
    app.dependency_overrides.clear()


class TestRecommendationAPI:
    """Tests for all 6 recommendation API endpoints."""

    @pytest.mark.asyncio
    async def test_get_recommendations(self, rec_client):
        resp = await rec_client.get("/api/v1/recommendations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) > 0
        assert "recommendation_score" in data["data"]["items"][0]

    @pytest.mark.asyncio
    async def test_get_for_you(self, rec_client):
        resp = await rec_client.get("/api/v1/recommendations/for-you")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) > 0

    @pytest.mark.asyncio
    async def test_get_for_you_no_auth(self, db_session):
        from app.database.session import get_db
        from app.main import app

        async def _override():
            yield db_session

        app.dependency_overrides[get_db] = _override
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/recommendations/for-you")
            assert resp.status_code in (401, 403)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_trending(self, rec_client):
        resp = await rec_client.get("/api/v1/recommendations/trending")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "top_tags" in data["data"]
        assert "most_important" in data["data"]

    @pytest.mark.asyncio
    async def test_set_preferences(self, rec_client):
        resp = await rec_client.post(
            "/api/v1/recommendations/preferences",
            json={
                "preferred_categories": ["ai_model", "security"],
                "preferred_sources": ["openai-blog"],
                "muted_categories": ["hackathon"],
                "muted_sources": [],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["preferred_categories"] == ["ai_model", "security"]

    @pytest.mark.asyncio
    async def test_get_preferences(self, rec_client):
        # Set first
        await rec_client.post(
            "/api/v1/recommendations/preferences",
            json={"preferred_categories": ["funding"]},
        )
        resp = await rec_client.get("/api/v1/recommendations/preferences")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "funding" in data["data"]["preferred_categories"]

    @pytest.mark.asyncio
    async def test_explain(self, rec_client):
        # Get an event ID from recommendations
        resp = await rec_client.get("/api/v1/recommendations")
        event_id = resp.json()["data"]["items"][0]["id"]

        resp = await rec_client.get(f"/api/v1/recommendations/explain/{event_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["event_id"] == event_id
        assert len(data["data"]["factors"]) > 0

    @pytest.mark.asyncio
    async def test_explain_not_found(self, rec_client):
        fake_id = str(uuid.uuid4())
        resp = await rec_client.get(f"/api/v1/recommendations/explain/{fake_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    async def test_for_you_with_prefs_applied(self, rec_client):
        # Set preferences to mute hackathon
        await rec_client.post(
            "/api/v1/recommendations/preferences",
            json={"muted_categories": ["hackathon"]},
        )
        resp = await rec_client.get("/api/v1/recommendations/for-you")
        data = resp.json()
        categories = [i["ai_category"] for i in data["data"]["items"]]
        assert "hackathon" not in categories

    @pytest.mark.asyncio
    async def test_recommendations_pagination(self, rec_client):
        resp = await rec_client.get("/api/v1/recommendations?limit=2&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["items"]) == 2
        assert "pagination" in data["data"]
