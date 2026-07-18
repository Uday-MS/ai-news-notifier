"""Unit and integration tests for the Search & Intelligence Feed (Sprint 5).

Tests cover:
- Feed repository (filters, sorting, pagination, aggregations)
- IntelligenceFeedService (search orchestration, validation)
- TrendingService (aggregation wrappers)
- API endpoints (via HTTPX test client)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import CollectedEvent, EventType
from app.models.processed_event import AICategory, ProcessedEvent, ProcessingStatus
from app.repositories.feed_repository import FeedRepository
from app.services.feed_service import IntelligenceFeedService, TrendingService


# ── Test Data Helpers ────────────────────────────────────────────────────


async def _seed_event(
    db: AsyncSession,
    *,
    title: str = "Test AI Event",
    summary: str = "A detailed summary of the AI event for testing purposes.",
    source: str = "test-blog",
    source_url: str | None = None,
    organization: str = "TestOrg",
    published_at: datetime | None = None,
    event_type: EventType = EventType.NEWS,
    tags: list[str] | None = None,
    # ProcessedEvent fields
    ai_category: AICategory = AICategory.AI_MODEL,
    ai_tags: list[str] | None = None,
    entities: dict | None = None,
    importance_score: int = 50,
    importance_reason: str = "Test score.",
    ai_summary: str = "AI summary of the event.",
    processing_status: ProcessingStatus = ProcessingStatus.READY,
) -> tuple[CollectedEvent, ProcessedEvent]:
    """Create a paired CollectedEvent + ProcessedEvent for testing."""
    if source_url is None:
        source_url = f"https://example.com/{uuid.uuid4()}"
    if published_at is None:
        published_at = datetime.now(timezone.utc)

    ce = CollectedEvent(
        title=title,
        summary=summary,
        source=source,
        source_url=source_url,
        published_at=published_at,
        event_type=event_type,
        organization=organization,
        tags=tags or [],
        extra_metadata={},
        collector_id="test",
        content_hash=str(uuid.uuid4())[:64],
    )
    db.add(ce)
    await db.flush()
    await db.refresh(ce)

    pe = ProcessedEvent(
        collected_event_id=ce.id,
        cleaned_title=title,
        cleaned_summary=summary,
        ai_category=ai_category,
        ai_tags=ai_tags or ["ai", "test"],
        entities=entities or {"organizations": [organization]},
        importance_score=importance_score,
        importance_reason=importance_reason,
        ai_summary=ai_summary,
        processing_status=processing_status,
        processed_at=datetime.now(timezone.utc),
    )
    db.add(pe)
    await db.flush()
    await db.refresh(pe)

    return ce, pe


async def _seed_diverse_events(db: AsyncSession) -> list[ProcessedEvent]:
    """Seed a diverse set of events for comprehensive testing."""
    now = datetime.now(timezone.utc)
    events = []

    _, pe1 = await _seed_event(
        db,
        title="OpenAI Launches GPT-5",
        summary="OpenAI released GPT-5 with multimodal support.",
        source="openai-blog",
        organization="OpenAI",
        published_at=now - timedelta(hours=1),
        ai_category=AICategory.AI_MODEL,
        ai_tags=["openai", "gpt-5", "llm", "multimodal"],
        entities={"organizations": ["OpenAI"], "models": ["GPT-5"]},
        importance_score=90,
    )
    events.append(pe1)

    _, pe2 = await _seed_event(
        db,
        title="Critical Security Vulnerability in ML Framework",
        summary="A zero-day exploit was discovered in a popular ML library.",
        source="security-blog",
        organization="SecurityTeam",
        published_at=now - timedelta(hours=2),
        ai_category=AICategory.SECURITY,
        ai_tags=["security", "vulnerability", "ml"],
        entities={"organizations": ["SecurityTeam"]},
        importance_score=85,
    )
    events.append(pe2)

    _, pe3 = await _seed_event(
        db,
        title="Global AI Hackathon 2025",
        summary="Register for the biggest AI hackathon with prizes worth $50K.",
        source="hackathon-site",
        organization="HackOrg",
        published_at=now - timedelta(hours=3),
        ai_category=AICategory.HACKATHON,
        ai_tags=["hackathon", "ai", "competition"],
        entities={"organizations": ["HackOrg"]},
        importance_score=60,
    )
    events.append(pe3)

    _, pe4 = await _seed_event(
        db,
        title="AI Startup Raises $100M Series B",
        summary="Leading AI startup secures major funding round.",
        source="tech-news",
        organization="FundedAI",
        published_at=now - timedelta(hours=4),
        ai_category=AICategory.FUNDING,
        ai_tags=["startup", "funding", "ai"],
        entities={"organizations": ["FundedAI"]},
        importance_score=70,
    )
    events.append(pe4)

    _, pe5 = await _seed_event(
        db,
        title="New Research Paper on Attention Mechanisms",
        summary="Researchers propose a novel attention mechanism.",
        source="arxiv",
        organization="MIT",
        published_at=now - timedelta(hours=5),
        ai_category=AICategory.AI_RESEARCH,
        ai_tags=["research", "attention", "transformer"],
        entities={"organizations": ["MIT"], "frameworks": ["PyTorch"]},
        importance_score=55,
    )
    events.append(pe5)

    # One FAILED event (should not appear in feed)
    _, pe6 = await _seed_event(
        db,
        title="Failed Event Should Not Appear",
        summary="This event failed processing.",
        source="unknown",
        organization="Unknown",
        published_at=now - timedelta(hours=6),
        ai_category=AICategory.OTHER,
        processing_status=ProcessingStatus.FAILED,
        importance_score=10,
    )
    events.append(pe6)

    await db.commit()
    return events


# ══════════════════════════════════════════════════════════════════════════
# Feed Repository Tests
# ══════════════════════════════════════════════════════════════════════════


class TestFeedRepository:
    """Tests for the feed repository query builder."""

    @pytest.mark.asyncio
    async def test_search_returns_only_ready(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        results = await repo.search()
        assert len(results) == 5  # 6 seeded, 1 FAILED excluded
        for item in results:
            assert item["processing_status"] == ProcessingStatus.READY

    @pytest.mark.asyncio
    async def test_search_keyword_title(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        results = await repo.search(keyword="GPT-5")
        assert len(results) == 1
        assert "GPT-5" in results[0]["cleaned_title"]

    @pytest.mark.asyncio
    async def test_search_keyword_summary(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        results = await repo.search(keyword="zero-day")
        assert len(results) == 1
        assert "Security" in results[0]["cleaned_title"]

    @pytest.mark.asyncio
    async def test_search_category_filter(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        results = await repo.search(category=AICategory.SECURITY.value)
        assert len(results) == 1
        assert results[0]["ai_category"] == AICategory.SECURITY

    @pytest.mark.asyncio
    async def test_search_source_filter(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        results = await repo.search(source="openai")
        assert len(results) == 1
        assert results[0]["source"] == "openai-blog"

    @pytest.mark.asyncio
    async def test_search_tag_filter(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        results = await repo.search(tag="hackathon")
        assert len(results) == 1
        assert "hackathon" in results[0]["ai_tags"]

    @pytest.mark.asyncio
    async def test_search_importance_range(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        results = await repo.search(importance_min=80)
        assert len(results) == 2  # 90 and 85
        for item in results:
            assert item["importance_score"] >= 80

    @pytest.mark.asyncio
    async def test_search_date_range(self, db_session):
        now = datetime.now(timezone.utc)
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        results = await repo.search(
            date_from=now - timedelta(hours=2, minutes=30),
            date_to=now,
        )
        # Events from 1h and 2h ago should match
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_sort_newest(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        results = await repo.search(sort="newest")
        dates = [r["published_at"] for r in results]
        assert dates == sorted(dates, reverse=True)

    @pytest.mark.asyncio
    async def test_search_sort_oldest(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        results = await repo.search(sort="oldest")
        dates = [r["published_at"] for r in results]
        assert dates == sorted(dates)

    @pytest.mark.asyncio
    async def test_search_sort_highest_importance(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        results = await repo.search(sort="highest_importance")
        scores = [r["importance_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_search_pagination(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        page1 = await repo.search(limit=2, offset=0)
        page2 = await repo.search(limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0]["id"] != page2[0]["id"]

    @pytest.mark.asyncio
    async def test_search_combined_filters(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        results = await repo.search(
            category=AICategory.AI_MODEL.value,
            importance_min=80,
        )
        assert len(results) == 1
        assert results[0]["ai_category"] == AICategory.AI_MODEL

    @pytest.mark.asyncio
    async def test_count_filtered(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        total = await repo.count_filtered()
        assert total == 5
        filtered = await repo.count_filtered(category=AICategory.SECURITY.value)
        assert filtered == 1

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session):
        events = await _seed_diverse_events(db_session)
        ready_event = events[0]  # First one is READY
        repo = FeedRepository(db_session)
        result = await repo.get_by_id(ready_event.id)
        assert result is not None
        assert result["id"] == ready_event.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session):
        repo = FeedRepository(db_session)
        result = await repo.get_by_id(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_top_categories(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        categories = await repo.top_categories()
        assert len(categories) == 5  # 5 distinct categories among READY
        assert all("category" in c and "count" in c for c in categories)

    @pytest.mark.asyncio
    async def test_most_important(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        results = await repo.most_important(limit=3)
        assert len(results) == 3
        scores = [r["importance_score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_top_tags(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        tags = await repo.top_tags()
        assert len(tags) > 0
        # "ai" appears in multiple events
        ai_tag = next((t for t in tags if t["tag"] == "ai"), None)
        assert ai_tag is not None
        assert ai_tag["count"] >= 2

    @pytest.mark.asyncio
    async def test_top_entities(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        entities = await repo.top_entities()
        assert len(entities) > 0
        assert all("entity" in e and "entity_type" in e and "count" in e for e in entities)

    @pytest.mark.asyncio
    async def test_count_ready(self, db_session):
        await _seed_diverse_events(db_session)
        repo = FeedRepository(db_session)
        count = await repo.count_ready()
        assert count == 5

    @pytest.mark.asyncio
    async def test_empty_search(self, db_session):
        repo = FeedRepository(db_session)
        results = await repo.search(keyword="nonexistent_keyword_xyz")
        assert results == []

    @pytest.mark.asyncio
    async def test_empty_database(self, db_session):
        repo = FeedRepository(db_session)
        results = await repo.search()
        assert results == []
        count = await repo.count_ready()
        assert count == 0


# ══════════════════════════════════════════════════════════════════════════
# Feed Service Tests
# ══════════════════════════════════════════════════════════════════════════


class TestIntelligenceFeedService:
    """Tests for the feed service orchestration."""

    @pytest.mark.asyncio
    async def test_get_feed(self, db_session):
        await _seed_diverse_events(db_session)
        service = IntelligenceFeedService(db_session)
        result = await service.get_feed()
        assert len(result.items) == 5
        assert result.pagination.total == 5
        assert result.pagination.has_more is False

    @pytest.mark.asyncio
    async def test_get_feed_pagination(self, db_session):
        await _seed_diverse_events(db_session)
        service = IntelligenceFeedService(db_session)
        result = await service.get_feed(limit=2, offset=0)
        assert len(result.items) == 2
        assert result.pagination.total == 5
        assert result.pagination.has_more is True

    @pytest.mark.asyncio
    async def test_search_with_keyword(self, db_session):
        await _seed_diverse_events(db_session)
        service = IntelligenceFeedService(db_session)
        result = await service.search(keyword="GPT-5")
        assert len(result.items) == 1
        assert result.pagination.total == 1

    @pytest.mark.asyncio
    async def test_search_with_category(self, db_session):
        await _seed_diverse_events(db_session)
        service = IntelligenceFeedService(db_session)
        result = await service.search(category=AICategory.HACKATHON.value)
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_search_invalid_sort_fallback(self, db_session):
        await _seed_diverse_events(db_session)
        service = IntelligenceFeedService(db_session)
        result = await service.search(sort="invalid_sort")
        # Should fall back to "newest" silently
        assert len(result.items) == 5

    @pytest.mark.asyncio
    async def test_search_importance_range_validation(self, db_session):
        service = IntelligenceFeedService(db_session)
        with pytest.raises(ValueError, match="importance_min"):
            await service.search(importance_min=80, importance_max=20)

    @pytest.mark.asyncio
    async def test_search_date_range_validation(self, db_session):
        service = IntelligenceFeedService(db_session)
        now = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="date_from"):
            await service.search(
                date_from=now,
                date_to=now - timedelta(days=1),
            )

    @pytest.mark.asyncio
    async def test_get_detail(self, db_session):
        events = await _seed_diverse_events(db_session)
        service = IntelligenceFeedService(db_session)
        detail = await service.get_detail(events[0].id)
        assert detail is not None
        assert detail.id == events[0].id
        assert detail.entities is not None
        assert detail.importance_reason

    @pytest.mark.asyncio
    async def test_get_detail_not_found(self, db_session):
        service = IntelligenceFeedService(db_session)
        detail = await service.get_detail(uuid.uuid4())
        assert detail is None


# ══════════════════════════════════════════════════════════════════════════
# Trending Service Tests
# ══════════════════════════════════════════════════════════════════════════


class TestTrendingService:
    """Tests for trending aggregations."""

    @pytest.mark.asyncio
    async def test_get_trending(self, db_session):
        await _seed_diverse_events(db_session)
        service = TrendingService(db_session)
        result = await service.get_trending()
        assert len(result.top_tags) > 0
        assert len(result.top_categories) > 0
        assert len(result.most_important) > 0
        assert result.total_ready == 5

    @pytest.mark.asyncio
    async def test_category_breakdown(self, db_session):
        await _seed_diverse_events(db_session)
        service = TrendingService(db_session)
        categories = await service.get_category_breakdown()
        assert len(categories) == 5
        assert all(c.count >= 1 for c in categories)

    @pytest.mark.asyncio
    async def test_entity_breakdown(self, db_session):
        await _seed_diverse_events(db_session)
        service = TrendingService(db_session)
        entities = await service.get_entity_breakdown()
        assert len(entities) > 0

    @pytest.mark.asyncio
    async def test_tag_cloud(self, db_session):
        await _seed_diverse_events(db_session)
        service = TrendingService(db_session)
        tags = await service.get_tag_cloud()
        assert len(tags) > 0
        # Tags should be sorted by count descending
        counts = [t.count for t in tags]
        assert counts == sorted(counts, reverse=True)

    @pytest.mark.asyncio
    async def test_trending_empty_db(self, db_session):
        service = TrendingService(db_session)
        result = await service.get_trending()
        assert result.total_ready == 0
        assert result.top_tags == []
        assert result.most_important == []


# ══════════════════════════════════════════════════════════════════════════
# API Endpoint Tests
# ══════════════════════════════════════════════════════════════════════════


@pytest_asyncio.fixture
async def seeded_client(db_session: AsyncSession):
    """Create a test HTTP client with seeded feed data."""
    from app.database.session import get_db
    from app.main import app

    await _seed_diverse_events(db_session)

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


class TestFeedAPI:
    """Tests for the feed API endpoints."""

    @pytest.mark.asyncio
    async def test_get_feed_endpoint(self, seeded_client):
        resp = await seeded_client.get("/api/v1/feed")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 5
        assert data["data"]["pagination"]["total"] == 5

    @pytest.mark.asyncio
    async def test_get_feed_pagination(self, seeded_client):
        resp = await seeded_client.get("/api/v1/feed?limit=2&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["items"]) == 2
        assert data["data"]["pagination"]["has_more"] is True

    @pytest.mark.asyncio
    async def test_search_endpoint(self, seeded_client):
        resp = await seeded_client.get("/api/v1/feed/search?q=GPT-5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 1

    @pytest.mark.asyncio
    async def test_search_category(self, seeded_client):
        resp = await seeded_client.get("/api/v1/feed/search?category=security")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["items"]) == 1

    @pytest.mark.asyncio
    async def test_search_source(self, seeded_client):
        resp = await seeded_client.get("/api/v1/feed/search?source=openai")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["items"]) == 1

    @pytest.mark.asyncio
    async def test_search_tag(self, seeded_client):
        resp = await seeded_client.get("/api/v1/feed/search?tag=hackathon")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["items"]) == 1

    @pytest.mark.asyncio
    async def test_search_importance(self, seeded_client):
        resp = await seeded_client.get("/api/v1/feed/search?importance_min=80")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["items"]) == 2

    @pytest.mark.asyncio
    async def test_search_sort(self, seeded_client):
        resp = await seeded_client.get("/api/v1/feed/search?sort=highest_importance")
        assert resp.status_code == 200
        data = resp.json()
        items = data["data"]["items"]
        scores = [i["importance_score"] for i in items]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_trending_endpoint(self, seeded_client):
        resp = await seeded_client.get("/api/v1/feed/trending")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "top_tags" in data["data"]
        assert "top_categories" in data["data"]
        assert "most_important" in data["data"]
        assert data["data"]["total_ready"] == 5

    @pytest.mark.asyncio
    async def test_categories_endpoint(self, seeded_client):
        resp = await seeded_client.get("/api/v1/feed/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]) == 5

    @pytest.mark.asyncio
    async def test_entities_endpoint(self, seeded_client):
        resp = await seeded_client.get("/api/v1/feed/entities")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]) > 0

    @pytest.mark.asyncio
    async def test_tags_endpoint(self, seeded_client):
        resp = await seeded_client.get("/api/v1/feed/tags")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]) > 0

    @pytest.mark.asyncio
    async def test_detail_endpoint(self, seeded_client):
        # First, get the feed to find an ID
        resp = await seeded_client.get("/api/v1/feed")
        item_id = resp.json()["data"]["items"][0]["id"]

        resp = await seeded_client.get(f"/api/v1/feed/{item_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["id"] == item_id
        assert "entities" in data["data"]
        assert "importance_reason" in data["data"]

    @pytest.mark.asyncio
    async def test_detail_not_found(self, seeded_client):
        fake_id = str(uuid.uuid4())
        resp = await seeded_client.get(f"/api/v1/feed/{fake_id}")
        assert resp.status_code == 200  # Envelope response
        data = resp.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_search_no_results(self, seeded_client):
        resp = await seeded_client.get("/api/v1/feed/search?q=nonexistent_xyz_123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 0
        assert data["data"]["pagination"]["total"] == 0
