"""End-to-end integration tests for the full AI News Notifier pipeline.

Tests the complete flow: Seed → Collect → Process → Feed → Recommendations →
Notifications → Delivery using mocked HTTP responses (no real network calls).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.collector_source import CollectorSource
from app.models.event import CollectedEvent, EventType
from app.models.notification import NotificationChannel
from app.models.processed_event import ProcessedEvent, ProcessingStatus, AICategory
from app.models.user import User, UserRole
from app.repositories.collector_source_repository import CollectorSourceRepository
from app.repositories.event_repository import EventRepository
from app.repositories.processed_event_repository import ProcessedEventRepository
from app.seeds.seed_sources import LIVE_AI_SOURCES, seed_sources
from app.services.collector_service import CollectorService
from app.services.delivery_service import NotificationDeliveryService
from app.services.feed_service import IntelligenceFeedService, TrendingService
from app.services.notification_service import NotificationService
from app.services.pipeline.pipeline_service import PipelineService
from app.services.recommendation_service import RecommendationService


# ── Mock RSS Feed Data ───────────────────────────────────────────────────

MOCK_RSS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test AI Blog</title>
    <link>https://example.com/blog</link>
    <description>Test AI News Feed</description>
    <item>
      <title>GPT-5 Announced: Next Generation Language Model</title>
      <link>https://example.com/blog/gpt-5-announced</link>
      <description>OpenAI has announced GPT-5, their next generation large language model with breakthrough reasoning capabilities and multimodal understanding.</description>
      <pubDate>Thu, 31 Jul 2026 10:00:00 GMT</pubDate>
      <category>AI</category>
      <category>Large Language Models</category>
    </item>
    <item>
      <title>Claude 4 Released with Advanced Code Understanding</title>
      <link>https://example.com/blog/claude-4-released</link>
      <description>Anthropic releases Claude 4 with significantly improved code generation, mathematical reasoning, and safety features built on constitutional AI principles.</description>
      <pubDate>Wed, 30 Jul 2026 14:00:00 GMT</pubDate>
      <category>AI Safety</category>
    </item>
    <item>
      <title>Google DeepMind Achieves Breakthrough in Protein Folding</title>
      <link>https://example.com/blog/deepmind-protein-folding</link>
      <description>Google DeepMind's AlphaFold 3 demonstrates unprecedented accuracy in predicting protein structures, opening new avenues for drug discovery and molecular biology.</description>
      <pubDate>Tue, 29 Jul 2026 09:00:00 GMT</pubDate>
      <category>Research</category>
    </item>
  </channel>
</rss>"""

MOCK_GITHUB_RELEASES = [
    {
        "name": "v2.5.0",
        "tag_name": "v2.5.0",
        "body": "Major release with new transformer architecture support and performance improvements.",
        "html_url": "https://github.com/test/ai-lib/releases/v2.5.0",
        "published_at": "2026-07-30T12:00:00Z",
        "author": {"login": "testdev"},
        "prerelease": False,
        "draft": False,
        "tarball_url": "https://github.com/test/ai-lib/tarball/v2.5.0",
    },
]


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def integration_user(db_session: AsyncSession) -> tuple[User, str]:
    """Create a user and return (user, access_token)."""
    user = User(
        id=uuid.uuid4(),
        email="integration_test@example.com",
        hashed_password=hash_password("StrongP@ss1"),
        full_name="Integration Test User",
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
async def integration_client(db_session: AsyncSession, integration_user):
    """Test HTTP client with auth."""
    from app.database.session import get_db
    from app.main import app

    user, token = integration_user

    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers["Authorization"] = f"Bearer {token}"
        yield ac, user
    app.dependency_overrides.clear()


def _mock_httpx_response(content: str | list, status_code: int = 200):
    """Create a mock httpx response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.raise_for_status = MagicMock()
    if isinstance(content, list):
        mock_response.json.return_value = content
        mock_response.text = str(content)
    else:
        mock_response.text = content
        mock_response.json.return_value = {}
    return mock_response


# ══════════════════════════════════════════════════════════════════════════
# Source Seeding Tests
# ══════════════════════════════════════════════════════════════════════════


class TestSourceSeeding:
    """Tests for the live AI source seed module."""

    @pytest.mark.asyncio
    async def test_seed_creates_all_sources(self, db_session):
        result = await seed_sources(db_session)
        assert result["created"] == len(LIVE_AI_SOURCES)
        assert result["skipped"] == 0
        assert result["total"] == len(LIVE_AI_SOURCES)

    @pytest.mark.asyncio
    async def test_seed_is_idempotent(self, db_session):
        # First run
        result1 = await seed_sources(db_session)
        assert result1["created"] == len(LIVE_AI_SOURCES)

        # Second run — all should be skipped
        result2 = await seed_sources(db_session)
        assert result2["created"] == 0
        assert result2["skipped"] == len(LIVE_AI_SOURCES)

    @pytest.mark.asyncio
    async def test_all_sources_have_valid_collector_types(self, db_session):
        from app.collectors.registry import collector_registry

        for source_def in LIVE_AI_SOURCES:
            assert collector_registry.get(source_def["collector_type"]) is not None, (
                f"Source '{source_def['name']}' has invalid collector_type: "
                f"'{source_def['collector_type']}'"
            )

    @pytest.mark.asyncio
    async def test_all_sources_are_active(self, db_session):
        await seed_sources(db_session)
        repo = CollectorSourceRepository(db_session)
        sources = await repo.get_active_sources()
        assert len(sources) == len(LIVE_AI_SOURCES)

    @pytest.mark.asyncio
    async def test_sources_have_organization_in_config(self):
        for source_def in LIVE_AI_SOURCES:
            assert "organization" in source_def["config"], (
                f"Source '{source_def['name']}' missing 'organization' in config"
            )

    @pytest.mark.asyncio
    async def test_seed_api_endpoint(self, db_session, integration_client):
        client, _ = integration_client
        resp = await client.post("/api/v1/integration/seed-sources")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["created"] == len(LIVE_AI_SOURCES)

    @pytest.mark.asyncio
    async def test_seed_api_idempotent(self, db_session, integration_client):
        client, _ = integration_client
        await client.post("/api/v1/integration/seed-sources")
        resp = await client.post("/api/v1/integration/seed-sources")
        data = resp.json()
        assert data["data"]["created"] == 0
        assert data["data"]["skipped"] == len(LIVE_AI_SOURCES)


# ══════════════════════════════════════════════════════════════════════════
# Collector Integration Tests
# ══════════════════════════════════════════════════════════════════════════


class TestCollectorIntegration:
    """Tests for collector with mocked HTTP responses."""

    @pytest.mark.asyncio
    async def test_rss_collector_with_mock_feed(self, db_session):
        """Collect from a mocked RSS feed and verify events are created."""
        # Register a test RSS source
        repo = CollectorSourceRepository(db_session)
        source = await repo.create(
            name="test-rss-source",
            collector_type="rss",
            url="https://example.com/feed.xml",
            config={"organization": "TestOrg", "event_type": "news"},
        )
        await db_session.commit()

        # Mock httpx to return our test feed
        mock_response = _mock_httpx_response(MOCK_RSS_FEED)
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.collectors.rss_collector.httpx.AsyncClient", return_value=mock_client):
            service = CollectorService(db_session)
            result = await service.run_collector(source.id)

        assert result.fetched == 3
        assert result.emitted == 3
        assert result.errors == 0

    @pytest.mark.asyncio
    async def test_blog_collector_with_mock_feed(self, db_session):
        """Collect from a mocked blog feed."""
        repo = CollectorSourceRepository(db_session)
        source = await repo.create(
            name="test-blog-source",
            collector_type="blog",
            url="https://example.com/blog/feed.xml",
            config={"organization": "TestBlog", "event_type": "blog_post"},
        )
        await db_session.commit()

        mock_response = _mock_httpx_response(MOCK_RSS_FEED)
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.collectors.blog_collector.httpx.AsyncClient", return_value=mock_client):
            service = CollectorService(db_session)
            result = await service.run_collector(source.id)

        assert result.fetched == 3
        assert result.emitted == 3

    @pytest.mark.asyncio
    async def test_github_collector_with_mock_api(self, db_session):
        """Collect from mocked GitHub releases API."""
        repo = CollectorSourceRepository(db_session)
        source = await repo.create(
            name="test-github-source",
            collector_type="github",
            url="https://api.github.com/repos/test/ai-lib/releases",
            config={"owner": "test", "repo": "ai-lib", "organization": "TestOrg"},
        )
        await db_session.commit()

        import json
        mock_response = _mock_httpx_response(MOCK_GITHUB_RELEASES)
        mock_response.json.return_value = MOCK_GITHUB_RELEASES
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.collectors.github_collector.httpx.AsyncClient", return_value=mock_client):
            service = CollectorService(db_session)
            result = await service.run_collector(source.id)

        assert result.fetched == 1
        assert result.emitted == 1

    @pytest.mark.asyncio
    async def test_deduplication_prevents_duplicates(self, db_session):
        """Running collector twice should not create duplicate events."""
        repo = CollectorSourceRepository(db_session)
        source = await repo.create(
            name="test-dedup-source",
            collector_type="rss",
            url="https://example.com/dedup-feed.xml",
            config={"organization": "TestOrg", "event_type": "news"},
        )
        await db_session.commit()

        mock_response = _mock_httpx_response(MOCK_RSS_FEED)
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.collectors.rss_collector.httpx.AsyncClient", return_value=mock_client):
            service = CollectorService(db_session)
            result1 = await service.run_collector(source.id)
            await db_session.commit()

            result2 = await service.run_collector(source.id)

        assert result1.emitted == 3
        assert result2.emitted == 0
        assert result2.duplicates == 3

    @pytest.mark.asyncio
    async def test_collector_handles_source_failure_gracefully(self, db_session):
        """Collector should handle network errors without crashing."""
        repo = CollectorSourceRepository(db_session)
        source = await repo.create(
            name="test-fail-source",
            collector_type="rss",
            url="https://example.com/failing-feed.xml",
            config={"organization": "TestOrg"},
        )
        await db_session.commit()

        import httpx
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.collectors.rss_collector.httpx.AsyncClient", return_value=mock_client):
            service = CollectorService(db_session)
            result = await service.run_collector(source.id)

        assert result.errors >= 1
        assert result.emitted == 0

    @pytest.mark.asyncio
    async def test_run_all_active_collects_from_multiple_sources(self, db_session):
        """run_all_active should collect from all active sources."""
        repo = CollectorSourceRepository(db_session)
        await repo.create(
            name="multi-source-1",
            collector_type="rss",
            url="https://example.com/feed1.xml",
            config={"organization": "Org1", "event_type": "news"},
        )
        await repo.create(
            name="multi-source-2",
            collector_type="rss",
            url="https://example.com/feed2.xml",
            config={"organization": "Org2", "event_type": "news"},
        )
        await db_session.commit()

        mock_response = _mock_httpx_response(MOCK_RSS_FEED)
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.collectors.rss_collector.httpx.AsyncClient", return_value=mock_client):
            service = CollectorService(db_session)
            results = await service.run_all_active()

        assert len(results) == 2
        # Both sources return the same mock articles (same URLs), so dedup
        # prevents the second source from re-emitting them.
        total_emitted = sum(r.get("emitted", 0) for r in results)
        total_fetched = sum(r.get("fetched", 0) for r in results)
        assert total_fetched == 6  # 3 fetched from each source
        assert total_emitted >= 3  # At least first source emits all 3


# ══════════════════════════════════════════════════════════════════════════
# Pipeline Integration Tests
# ══════════════════════════════════════════════════════════════════════════


class TestPipelineIntegration:
    """Tests that collected events are processed correctly through the pipeline."""

    async def _seed_collected_events(self, db_session) -> list[CollectedEvent]:
        """Create collected events directly for pipeline testing."""
        events = []
        for i, (title, summary, org) in enumerate([
            (
                "GPT-5 Announced: Next Generation Language Model",
                "OpenAI has announced GPT-5 with breakthrough reasoning capabilities.",
                "OpenAI",
            ),
            (
                "PyTorch 3.0 Released with Native Compiler",
                "Meta releases PyTorch 3.0 with a native compiler for faster training.",
                "Meta AI",
            ),
            (
                "New Research Paper on Transformer Efficiency",
                "Researchers propose a novel attention mechanism reducing compute by 40%.",
                "arXiv",
            ),
        ]):
            event = CollectedEvent(
                title=title,
                summary=summary,
                source=f"test-source-{i}",
                source_url=f"https://example.com/article-{i}-{uuid.uuid4().hex[:8]}",
                published_at=datetime.now(timezone.utc),
                event_type=EventType.NEWS,
                organization=org,
                tags=["ai", "machine-learning"],
                extra_metadata={},
                collector_id="test",
                content_hash=uuid.uuid4().hex,
            )
            db_session.add(event)
            events.append(event)
        await db_session.flush()
        for e in events:
            await db_session.refresh(e)
        return events

    @pytest.mark.asyncio
    async def test_process_all_unprocessed(self, db_session):
        events = await self._seed_collected_events(db_session)
        await db_session.commit()

        service = PipelineService(db_session)
        summary = await service.process_all_unprocessed()

        assert summary["total"] == 3
        assert summary["processed"] == 3
        assert summary["failed"] == 0

    @pytest.mark.asyncio
    async def test_processed_events_have_required_fields(self, db_session):
        events = await self._seed_collected_events(db_session)
        await db_session.commit()

        service = PipelineService(db_session)
        await service.process_all_unprocessed()

        repo = ProcessedEventRepository(db_session)
        for event in events:
            pe = await repo.get_by_collected_event_id(event.id)
            assert pe is not None
            assert pe.cleaned_title
            assert pe.cleaned_summary
            assert pe.ai_category is not None
            assert isinstance(pe.ai_tags, list)
            assert isinstance(pe.entities, dict)
            assert pe.importance_score >= 0
            assert pe.processing_status in (
                ProcessingStatus.READY, ProcessingStatus.PARTIAL
            )

    @pytest.mark.asyncio
    async def test_pipeline_idempotent(self, db_session):
        """Processing same event twice re-processes (updates) it."""
        events = await self._seed_collected_events(db_session)
        await db_session.commit()

        service = PipelineService(db_session)
        await service.process_all_unprocessed()

        # Second run should find 0 unprocessed
        summary = await service.process_all_unprocessed()
        assert summary["total"] == 0


# ══════════════════════════════════════════════════════════════════════════
# Feed Integration Tests
# ══════════════════════════════════════════════════════════════════════════


class TestFeedIntegration:
    """Tests that processed events appear in the feed."""

    async def _seed_processed_events(self, db_session) -> list[ProcessedEvent]:
        """Create collected + processed events for feed testing."""
        processed = []
        for i in range(3):
            ce = CollectedEvent(
                title=f"Feed Test Article {i}",
                summary=f"Summary for article {i} about AI breakthroughs.",
                source=f"feed-source-{i}",
                source_url=f"https://example.com/feed-article-{i}-{uuid.uuid4().hex[:8]}",
                published_at=datetime.now(timezone.utc),
                event_type=EventType.NEWS,
                organization="TestOrg",
                tags=["ai"],
                extra_metadata={},
                collector_id="test",
                content_hash=uuid.uuid4().hex,
            )
            db_session.add(ce)
            await db_session.flush()
            await db_session.refresh(ce)

            pe = ProcessedEvent(
                collected_event_id=ce.id,
                cleaned_title=f"Feed Test Article {i}",
                cleaned_summary=f"Summary for article {i} about AI breakthroughs.",
                ai_category=AICategory.AI_MODEL,
                ai_tags=["ai", "machine-learning", "deep-learning"],
                entities={"organizations": ["TestOrg"]},
                importance_score=70 + i * 10,
                importance_reason="High relevance.",
                ai_summary=f"AI summary for article {i}.",
                processing_status=ProcessingStatus.READY,
                processed_at=datetime.now(timezone.utc),
            )
            db_session.add(pe)
            processed.append(pe)

        await db_session.flush()
        for p in processed:
            await db_session.refresh(p)
        return processed

    @pytest.mark.asyncio
    async def test_feed_returns_processed_events(self, db_session):
        await self._seed_processed_events(db_session)
        await db_session.commit()

        service = IntelligenceFeedService(db_session)
        result = await service.get_feed(limit=50)
        assert len(result.items) == 3

    @pytest.mark.asyncio
    async def test_feed_search_by_keyword(self, db_session):
        await self._seed_processed_events(db_session)
        await db_session.commit()

        service = IntelligenceFeedService(db_session)
        result = await service.search(keyword="AI breakthroughs")
        assert len(result.items) >= 1

    @pytest.mark.asyncio
    async def test_trending_returns_data(self, db_session):
        await self._seed_processed_events(db_session)
        await db_session.commit()

        service = TrendingService(db_session)
        result = await service.get_trending()
        assert result.total_ready == 3
        assert len(result.most_important) > 0


# ══════════════════════════════════════════════════════════════════════════
# Full Pipeline End-to-End Tests
# ══════════════════════════════════════════════════════════════════════════


class TestEndToEndPipeline:
    """Tests the complete flow: Collect → Process → Feed → Recommend → Notify → Deliver."""

    @pytest.mark.asyncio
    async def test_collect_process_feed_roundtrip(self, db_session, integration_user):
        """Full roundtrip: collect → process → verify in feed."""
        user, _ = integration_user

        # 1. Register source
        source_repo = CollectorSourceRepository(db_session)
        source = await source_repo.create(
            name="e2e-rss-source",
            collector_type="rss",
            url="https://example.com/e2e-feed.xml",
            config={"organization": "E2E Org", "event_type": "news"},
        )
        await db_session.commit()

        # 2. Collect with mocked HTTP
        mock_response = _mock_httpx_response(MOCK_RSS_FEED)
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.collectors.rss_collector.httpx.AsyncClient", return_value=mock_client):
            collector = CollectorService(db_session)
            collect_result = await collector.run_collector(source.id)

        assert collect_result.emitted == 3
        await db_session.commit()

        # 3. Process through pipeline
        pipeline = PipelineService(db_session)
        pipeline_result = await pipeline.process_all_unprocessed()
        assert pipeline_result["processed"] == 3
        await db_session.commit()

        # 4. Verify in feed
        feed = IntelligenceFeedService(db_session)
        feed_result = await feed.get_feed(limit=50)
        assert len(feed_result.items) == 3

        # 5. Verify trending
        trending = TrendingService(db_session)
        trending_result = await trending.get_trending()
        assert trending_result.total_ready == 3

    @pytest.mark.asyncio
    async def test_full_pipeline_with_notifications(self, db_session, integration_user):
        """Full pipeline including recommendation → notification → delivery."""
        user, _ = integration_user

        # Seed collected + processed events directly
        ce = CollectedEvent(
            title="Major AI Breakthrough in Reasoning",
            summary="A new model achieves superhuman reasoning on complex benchmarks.",
            source="test-source",
            source_url=f"https://example.com/breakthrough-{uuid.uuid4().hex[:8]}",
            published_at=datetime.now(timezone.utc),
            event_type=EventType.NEWS,
            organization="OpenAI",
            tags=["ai", "reasoning"],
            extra_metadata={},
            collector_id="test",
            content_hash=uuid.uuid4().hex,
        )
        db_session.add(ce)
        await db_session.flush()
        await db_session.refresh(ce)

        pe = ProcessedEvent(
            collected_event_id=ce.id,
            cleaned_title="Major AI Breakthrough in Reasoning",
            cleaned_summary="A new model achieves superhuman reasoning on complex benchmarks.",
            ai_category=AICategory.AI_MODEL,
            ai_tags=["ai", "reasoning", "benchmarks"],
            entities={"organizations": ["OpenAI"]},
            importance_score=95,
            importance_reason="Major breakthrough from top AI lab.",
            ai_summary="OpenAI achieves superhuman reasoning.",
            processing_status=ProcessingStatus.READY,
            processed_at=datetime.now(timezone.utc),
        )
        db_session.add(pe)
        await db_session.flush()
        await db_session.refresh(pe)
        await db_session.commit()

        # Generate notification directly via repository (the service
        # generate_for_user() needs the full recommendation engine;
        # here we test the notification→delivery path directly)
        from app.models.notification import Notification, NotificationType
        from app.repositories.notification_repository import NotificationRepository

        notif_repo = NotificationRepository(db_session)
        notification = await notif_repo.create(
            Notification(
                user_id=user.id,
                processed_event_id=pe.id,
                notification_type=NotificationType.RECOMMENDATION,
                channel=NotificationChannel.IN_APP,
                title="Major AI Breakthrough in Reasoning",
                message="OpenAI achieves superhuman reasoning.",
                recommendation_score=95.0,
            )
        )
        assert notification is not None
        assert notification.title

        # Deliver notification
        delivery = NotificationDeliveryService(db_session)
        delivery_result = await delivery.send(notification.id, user.id)
        assert delivery_result.success is True
        assert delivery_result.delivered_at is not None

        # Verify status
        status = await delivery.get_delivery_status(notification.id, user.id)
        assert status["status"] == "delivered"


# ══════════════════════════════════════════════════════════════════════════
# API Integration Tests
# ══════════════════════════════════════════════════════════════════════════


class TestIntegrationAPI:
    """Tests for the integration API endpoints."""

    @pytest.mark.asyncio
    async def test_collect_and_process_endpoint(self, db_session, integration_client):
        """Test the collect-and-process orchestration endpoint."""
        client, _ = integration_client

        # Seed a source first
        source_repo = CollectorSourceRepository(db_session)
        await source_repo.create(
            name="api-e2e-source",
            collector_type="rss",
            url="https://example.com/api-feed.xml",
            config={"organization": "APIOrg", "event_type": "news"},
        )
        await db_session.commit()

        # Mock HTTP for collector
        mock_response = _mock_httpx_response(MOCK_RSS_FEED)
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.collectors.rss_collector.httpx.AsyncClient", return_value=mock_client):
            resp = await client.post("/api/v1/integration/collect-and-process")

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["collection"]["total_emitted"] == 3
        assert data["data"]["processing"]["processed"] == 3

    @pytest.mark.asyncio
    async def test_integration_status_endpoint(self, db_session, integration_client):
        """Test the status dashboard endpoint."""
        client, _ = integration_client
        resp = await client.get("/api/v1/integration/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "collected_events" in data["data"]
        assert "processed_events" in data["data"]
        assert "notifications" in data["data"]

    @pytest.mark.asyncio
    async def test_status_counts_increase_after_collection(self, db_session, integration_client):
        """Status counts should reflect data after collect-and-process."""
        client, _ = integration_client

        # Check initial status
        resp = await client.get("/api/v1/integration/status")
        initial = resp.json()["data"]
        assert initial["collected_events"] == 0

        # Seed + collect
        source_repo = CollectorSourceRepository(db_session)
        await source_repo.create(
            name="status-test-source",
            collector_type="rss",
            url="https://example.com/status-feed.xml",
            config={"organization": "StatusOrg", "event_type": "news"},
        )
        await db_session.commit()

        mock_response = _mock_httpx_response(MOCK_RSS_FEED)
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("app.collectors.rss_collector.httpx.AsyncClient", return_value=mock_client):
            await client.post("/api/v1/integration/collect-and-process")

        # Check updated status
        resp = await client.get("/api/v1/integration/status")
        updated = resp.json()["data"]
        assert updated["collected_events"] == 3
        assert updated["processed_events"] == 3
        assert updated["unprocessed_events"] == 0

    @pytest.mark.asyncio
    async def test_no_auth_returns_error(self, db_session):
        """Integration endpoints require authentication."""
        from app.database.session import get_db
        from app.main import app

        async def _override():
            yield db_session

        app.dependency_overrides[get_db] = _override
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/v1/integration/seed-sources")
            assert resp.status_code in (401, 403)

            resp = await ac.post("/api/v1/integration/collect-and-process")
            assert resp.status_code in (401, 403)

            resp = await ac.get("/api/v1/integration/status")
            assert resp.status_code in (401, 403)
        app.dependency_overrides.clear()
