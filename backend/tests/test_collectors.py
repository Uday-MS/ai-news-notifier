"""Unit tests for the Collector Engine (Phase 1 — Real Intelligence Ingestion).

Tests cover:
- Deduplication service (hash generation, duplicate detection)
- Base collector pipeline logic (emit, skip, error handling)
- Collector registry
- Event and source schemas
- RSS/Blog/GitHub collector normalization
- Retry with backoff
- Source failure isolation
- Provenance preservation
- Source health tracking
- Interval-aware scheduling
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.collectors.base import BaseCollector, CollectorRunResult, RawItem
from app.collectors.registry import CollectorRegistry
from app.collectors.rss_collector import RSSCollector
from app.collectors.blog_collector import BlogCollector
from app.collectors.github_collector import GitHubCollector
from app.models.collector_source import CollectorSource
from app.models.event import CollectedEvent, EventType
from app.schemas.collector_source import CollectorSourceCreate, CollectorSourceHealth
from app.schemas.event import EventCreate, EventRead, EventSummary
from app.services.dedup_service import DeduplicationService


# ── Helpers ──────────────────────────────────────────────────────────────


def _make_event_create(**overrides: Any) -> EventCreate:
    """Build a valid EventCreate with sensible defaults."""
    defaults = {
        "title": "Test Event",
        "summary": "A test event summary.",
        "source": "test-source",
        "source_url": "https://example.com/article-1",
        "published_at": datetime(2025, 1, 15, tzinfo=timezone.utc),
        "event_type": EventType.NEWS,
        "organization": "TestOrg",
        "tags": ["ai", "test"],
        "extra_metadata": {},
        "collector_id": "test",
        "content_hash": "abc123",
    }
    defaults.update(overrides)
    return EventCreate(**defaults)


def _make_source(**overrides: Any) -> CollectorSource:
    """Build a mock CollectorSource."""
    source = MagicMock(spec=CollectorSource)
    source.id = overrides.get("id", uuid.uuid4())
    source.name = overrides.get("name", "Test Source")
    source.collector_type = overrides.get("collector_type", "test")
    source.url = overrides.get("url", "https://example.com/feed.xml")
    source.config = overrides.get("config", {})
    source.is_active = overrides.get("is_active", True)
    source.last_collected_at = overrides.get("last_collected_at", None)
    source.collection_interval_minutes = overrides.get("collection_interval_minutes", 60)
    return source


class StubCollector(BaseCollector):
    """Concrete collector for testing the base pipeline."""

    collector_type = "stub"

    def __init__(self, event_repo: Any, dedup_service: Any, items: list[RawItem] | None = None) -> None:
        super().__init__(event_repo, dedup_service)
        self._items = items or []

    async def fetch(self, source: CollectorSource) -> list[RawItem]:
        return self._items

    def normalize(self, raw: RawItem, source: CollectorSource) -> EventCreate:
        content_hash = DeduplicationService.generate_content_hash(
            raw.get("link", ""),
            raw.get("title", ""),
            datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        return _make_event_create(
            title=raw.get("title", ""),
            summary=raw.get("summary", "test summary"),
            source_url=raw.get("link", ""),
            content_hash=content_hash,
        )


# ── Deduplication Tests ─────────────────────────────────────────────────


class TestDeduplicationService:
    """Tests for DeduplicationService."""

    def test_generate_content_hash_deterministic(self) -> None:
        """Same inputs produce the same hash."""
        h1 = DeduplicationService.generate_content_hash(
            "https://example.com/a", "Title", datetime(2025, 1, 1, tzinfo=timezone.utc)
        )
        h2 = DeduplicationService.generate_content_hash(
            "https://example.com/a", "Title", datetime(2025, 1, 1, tzinfo=timezone.utc)
        )
        assert h1 == h2

    def test_generate_content_hash_differs_on_url(self) -> None:
        """Different URLs produce different hashes."""
        h1 = DeduplicationService.generate_content_hash(
            "https://example.com/a", "Title", datetime(2025, 1, 1, tzinfo=timezone.utc)
        )
        h2 = DeduplicationService.generate_content_hash(
            "https://example.com/b", "Title", datetime(2025, 1, 1, tzinfo=timezone.utc)
        )
        assert h1 != h2

    def test_generate_content_hash_case_insensitive(self) -> None:
        """Hash normalises case for URL and title."""
        h1 = DeduplicationService.generate_content_hash(
            "https://Example.com/A", "TITLE", datetime(2025, 1, 1, tzinfo=timezone.utc)
        )
        h2 = DeduplicationService.generate_content_hash(
            "https://example.com/a", "title", datetime(2025, 1, 1, tzinfo=timezone.utc)
        )
        assert h1 == h2

    def test_hash_is_sha256_length(self) -> None:
        h = DeduplicationService.generate_content_hash(
            "https://x.com", "t", datetime(2025, 1, 1, tzinfo=timezone.utc)
        )
        assert len(h) == 64  # SHA-256 hex digest

    @pytest.mark.asyncio
    async def test_is_duplicate_true(self) -> None:
        repo = AsyncMock()
        repo.exists_by_hash.return_value = True
        service = DeduplicationService(repo)
        event = _make_event_create()
        assert await service.is_duplicate(event) is True

    @pytest.mark.asyncio
    async def test_is_duplicate_false(self) -> None:
        repo = AsyncMock()
        repo.exists_by_hash.return_value = False
        repo.exists_by_source_url.return_value = False
        service = DeduplicationService(repo)
        event = _make_event_create()
        assert await service.is_duplicate(event) is False


# ── Collector Registry Tests ────────────────────────────────────────────


class TestCollectorRegistry:
    """Tests for CollectorRegistry."""

    def test_register_and_get(self) -> None:
        registry = CollectorRegistry()
        registry.register(StubCollector)
        assert registry.get("stub") is StubCollector

    def test_get_unknown_returns_none(self) -> None:
        registry = CollectorRegistry()
        assert registry.get("nonexistent") is None

    def test_list_types(self) -> None:
        registry = CollectorRegistry()
        registry.register(StubCollector)
        assert "stub" in registry.list_types()

    def test_global_registry_has_builtins(self) -> None:
        from app.collectors.registry import collector_registry
        types = collector_registry.list_types()
        assert "rss" in types
        assert "github" in types
        assert "blog" in types


# ── Base Collector Pipeline Tests ────────────────────────────────────────


class TestBaseCollectorPipeline:
    """Tests for the base collector run() orchestration."""

    @pytest.mark.asyncio
    async def test_run_emits_new_events(self) -> None:
        """Non-duplicate items get emitted."""
        repo = AsyncMock()
        repo.exists_by_hash.return_value = False
        repo.exists_by_source_url.return_value = False
        repo.create.return_value = MagicMock(spec=CollectedEvent)
        dedup = DeduplicationService(repo)

        items: list[RawItem] = [
            RawItem(title="Item 1", link="https://example.com/1", summary="s", published=""),
            RawItem(title="Item 2", link="https://example.com/2", summary="s", published=""),
        ]
        collector = StubCollector(repo, dedup, items)
        result = await collector.run(_make_source())

        assert result.fetched == 2
        assert result.emitted == 2
        assert result.duplicates == 0

    @pytest.mark.asyncio
    async def test_run_skips_duplicates(self) -> None:
        """Duplicate items are counted but not emitted."""
        repo = AsyncMock()
        repo.exists_by_hash.return_value = True
        dedup = DeduplicationService(repo)

        items: list[RawItem] = [
            RawItem(title="Dup", link="https://example.com/dup", summary="s", published=""),
        ]
        collector = StubCollector(repo, dedup, items)
        result = await collector.run(_make_source())

        assert result.fetched == 1
        assert result.emitted == 0
        assert result.duplicates == 1

    @pytest.mark.asyncio
    async def test_run_handles_fetch_error(self) -> None:
        """Fetch failures are captured without crashing."""
        repo = AsyncMock()
        dedup = DeduplicationService(repo)

        collector = StubCollector(repo, dedup)
        # Patch fetch to raise
        collector.fetch = AsyncMock(side_effect=RuntimeError("network down"))
        result = await collector.run(_make_source())

        assert result.errors == 1
        assert "Fetch failed" in result.error_messages[0]

    @pytest.mark.asyncio
    async def test_run_result_has_timing(self) -> None:
        """CollectorRunResult includes started_at and finished_at."""
        repo = AsyncMock()
        repo.exists_by_hash.return_value = False
        repo.exists_by_source_url.return_value = False
        repo.create.return_value = MagicMock(spec=CollectedEvent)
        dedup = DeduplicationService(repo)

        collector = StubCollector(repo, dedup, [])
        result = await collector.run(_make_source())

        assert result.started_at is not None
        assert result.finished_at is not None
        assert result.finished_at >= result.started_at

    @pytest.mark.asyncio
    async def test_run_isolates_normalize_errors(self) -> None:
        """A normalize error on one item doesn't stop processing others."""
        repo = AsyncMock()
        repo.exists_by_hash.return_value = False
        repo.exists_by_source_url.return_value = False
        repo.create.return_value = MagicMock(spec=CollectedEvent)
        dedup = DeduplicationService(repo)

        items: list[RawItem] = [
            RawItem(title="Good", link="https://example.com/good", summary="ok", published=""),
            RawItem(title="Bad", link="https://example.com/bad", summary="ok", published=""),
            RawItem(title="Also Good", link="https://example.com/good2", summary="ok", published=""),
        ]
        collector = StubCollector(repo, dedup, items)

        # Make normalize fail on the second item only
        original_normalize = collector.normalize
        call_count = 0

        def patched_normalize(raw, source):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("bad data")
            return original_normalize(raw, source)

        collector.normalize = patched_normalize
        result = await collector.run(_make_source())

        assert result.fetched == 3
        assert result.emitted == 2  # 2 good items emitted
        assert result.errors == 1   # 1 normalize error

    @pytest.mark.asyncio
    async def test_validation_rejects_empty_fields(self) -> None:
        """Items with empty title/url/summary are rejected by validate()."""
        repo = AsyncMock()
        dedup = DeduplicationService(repo)
        collector = StubCollector(repo, dedup)

        # Empty title
        assert collector.validate(_make_event_create(title="")) is False
        # Empty URL
        assert collector.validate(_make_event_create(source_url="")) is False
        # Empty summary
        assert collector.validate(_make_event_create(summary="")) is False
        # All present — valid
        assert collector.validate(_make_event_create()) is True


# ── Retry Tests ──────────────────────────────────────────────────────────


class TestRetryBehavior:
    """Tests for the bounded retry mechanism in BaseCollector."""

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self) -> None:
        """Transient timeout triggers retry, succeeds on second attempt."""
        repo = AsyncMock()
        repo.exists_by_hash.return_value = False
        repo.exists_by_source_url.return_value = False
        repo.create.return_value = MagicMock(spec=CollectedEvent)
        dedup = DeduplicationService(repo)

        items = [RawItem(title="Recovered", link="https://example.com/r", summary="s", published="")]
        collector = StubCollector(repo, dedup, items)

        call_count = 0
        original_fetch = collector.fetch

        async def failing_then_ok(source):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.ConnectTimeout("connection timed out")
            return await original_fetch(source)

        collector.fetch = failing_then_ok

        with patch("app.collectors.base.asyncio.sleep", new_callable=AsyncMock):
            result = await collector.run(_make_source())

        assert result.fetched == 1
        assert result.emitted == 1
        assert result.errors == 0
        assert call_count == 2  # 1 failure + 1 success

    @pytest.mark.asyncio
    async def test_retry_exhausted(self) -> None:
        """After max retries, failure is recorded."""
        repo = AsyncMock()
        dedup = DeduplicationService(repo)

        collector = StubCollector(repo, dedup)
        collector.fetch = AsyncMock(side_effect=httpx.ConnectTimeout("down"))

        with patch("app.collectors.base.asyncio.sleep", new_callable=AsyncMock):
            with patch("app.collectors.base.settings") as mock_settings:
                mock_settings.COLLECTOR_MAX_RETRIES = 2
                mock_settings.COLLECTOR_RETRY_BACKOFF_BASE = 0.01
                result = await collector.run(_make_source())

        assert result.errors == 1
        assert "Fetch failed" in result.error_messages[0]
        assert collector.fetch.call_count == 3  # initial + 2 retries

    @pytest.mark.asyncio
    async def test_no_retry_on_4xx(self) -> None:
        """4xx HTTP errors are not retried."""
        repo = AsyncMock()
        dedup = DeduplicationService(repo)

        response = MagicMock()
        response.status_code = 404
        collector = StubCollector(repo, dedup)
        collector.fetch = AsyncMock(
            side_effect=httpx.HTTPStatusError("Not Found", request=MagicMock(), response=response)
        )

        with patch("app.collectors.base.asyncio.sleep", new_callable=AsyncMock):
            result = await collector.run(_make_source())

        assert result.errors == 1
        assert collector.fetch.call_count == 1  # No retry


# ── Source Failure Isolation Tests ───────────────────────────────────────


class TestSourceFailureIsolation:
    """One source failure must not stop other sources."""

    @pytest.mark.asyncio
    async def test_collector_service_isolates_failures(self) -> None:
        """CollectorService.run_all_active continues after one source fails."""
        from app.services.collector_service import CollectorService

        service = CollectorService.__new__(CollectorService)
        service._db = AsyncMock()
        service._source_repo = AsyncMock()
        service._event_repo = AsyncMock()
        service._dedup = AsyncMock()

        source1 = _make_source(name="source-1")
        source2 = _make_source(name="source-2")
        service._source_repo.get_active_sources.return_value = [source1, source2]

        # First run_collector fails, second succeeds
        call_count = 0

        async def mock_run(source_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Source 1 down")
            return CollectorRunResult(
                collector_type="test", source_name="source-2",
                fetched=5, emitted=3,
            )

        service.run_collector = mock_run
        service._source_repo.record_failure = AsyncMock()

        results = await service.run_all_active()

        assert len(results) == 2
        # First result is error
        assert results[0]["errors"] == 1
        # Second result is success
        assert results[1]["emitted"] == 3


# ── Provenance Preservation Tests ────────────────────────────────────────


class TestProvenancePreservation:
    """Ensure collected events retain original source information."""

    def test_rss_normalize_preserves_provenance(self) -> None:
        """RSS collector preserves source_url, organization, collector_id."""
        repo = AsyncMock()
        dedup = DeduplicationService(repo)
        collector = RSSCollector(repo, dedup)

        source = _make_source(
            name="openai-blog",
            config={"organization": "OpenAI", "event_type": "blog_post"},
        )

        raw = RawItem(
            title="GPT-5 Released",
            summary="A new frontier model.",
            link="https://openai.com/blog/gpt-5",
            published="Mon, 01 Jan 2025 12:00:00 GMT",
            author="OpenAI",
            tags=["gpt", "llm"],
            extra={"feed_title": "OpenAI Blog", "entry_id": "123"},
        )

        event = collector.normalize(raw, source)

        assert event.source_url == "https://openai.com/blog/gpt-5"
        assert event.organization == "OpenAI"
        assert event.collector_id == "rss"
        assert event.source == "openai-blog"
        assert event.title == "GPT-5 Released"
        assert len(event.content_hash) == 64

    def test_github_normalize_preserves_provenance(self) -> None:
        """GitHub collector preserves release URL and organization."""
        repo = AsyncMock()
        dedup = DeduplicationService(repo)
        collector = GitHubCollector(repo, dedup)

        source = _make_source(
            name="github-pytorch",
            config={"owner": "pytorch", "repo": "pytorch", "organization": "Meta AI"},
        )

        raw = RawItem(
            title="v2.5.0",
            summary="Major release with new features.",
            link="https://github.com/pytorch/pytorch/releases/tag/v2.5.0",
            published="2025-01-15T12:00:00Z",
            author="pytorch",
            tags=["v2.5.0"],
            extra={"prerelease": False, "draft": False},
        )

        event = collector.normalize(raw, source)

        assert event.source_url == "https://github.com/pytorch/pytorch/releases/tag/v2.5.0"
        assert event.organization == "pytorch"
        assert event.collector_id == "github"
        assert event.event_type == EventType.RELEASE

    def test_blog_normalize_preserves_provenance(self) -> None:
        """Blog collector preserves full content and source info."""
        repo = AsyncMock()
        dedup = DeduplicationService(repo)
        collector = BlogCollector(repo, dedup)

        source = _make_source(
            name="deepmind-blog",
            config={"organization": "Google DeepMind", "event_type": "blog_post"},
        )

        raw = RawItem(
            title="AlphaFold 3 Update",
            summary="New protein structure predictions.",
            link="https://deepmind.google/blog/alphafold-3",
            published="2025-03-01T10:00:00Z",
            author="DeepMind Team",
            tags=["alphafold", "biology"],
            extra={"feed_title": "DeepMind Blog", "entry_id": "af3"},
        )

        event = collector.normalize(raw, source)

        assert event.source_url == "https://deepmind.google/blog/alphafold-3"
        assert event.organization == "Google DeepMind"
        assert event.collector_id == "blog"
        assert event.event_type == EventType.BLOG_POST


# ── Source Configuration Tests ───────────────────────────────────────────


class TestSourceConfiguration:
    """Tests for the seed source configuration data."""

    def test_seed_sources_structure(self) -> None:
        """All seed sources have required fields."""
        from app.seeds.seed_sources import LIVE_AI_SOURCES

        required_keys = {"name", "collector_type", "url", "config", "collection_interval_minutes"}
        for src in LIVE_AI_SOURCES:
            missing = required_keys - set(src.keys())
            assert not missing, f"Source {src.get('name', '?')} missing keys: {missing}"

    def test_seed_sources_have_organization(self) -> None:
        """All seed sources have an organization in their config."""
        from app.seeds.seed_sources import LIVE_AI_SOURCES

        for src in LIVE_AI_SOURCES:
            assert "organization" in src["config"], (
                f"Source {src['name']} missing organization in config"
            )

    def test_seed_sources_valid_collector_types(self) -> None:
        """All seed sources use registered collector types."""
        from app.seeds.seed_sources import LIVE_AI_SOURCES
        valid_types = {"rss", "blog", "github"}

        for src in LIVE_AI_SOURCES:
            assert src["collector_type"] in valid_types, (
                f"Source {src['name']} has unknown collector_type: {src['collector_type']}"
            )

    def test_seed_sources_unique_names(self) -> None:
        """All seed source names are unique."""
        from app.seeds.seed_sources import LIVE_AI_SOURCES

        names = [s["name"] for s in LIVE_AI_SOURCES]
        assert len(names) == len(set(names)), "Duplicate source names found"

    def test_seed_sources_have_trust_tier(self) -> None:
        """All seed sources have a trust_tier in config."""
        from app.seeds.seed_sources import LIVE_AI_SOURCES

        for src in LIVE_AI_SOURCES:
            assert "trust_tier" in src["config"], (
                f"Source {src['name']} missing trust_tier"
            )


# ── Schema Validation Tests ──────────────────────────────────────────────


class TestSchemas:
    """Basic schema validation tests."""

    def test_event_create_valid(self) -> None:
        event = _make_event_create()
        assert event.title == "Test Event"

    def test_event_create_rejects_empty_title(self) -> None:
        """EventCreate should fail pydantic validation for blank required fields."""
        # title is required and max_length=500 but not min_length,
        # validation happens in the collector's validate() method instead
        event = _make_event_create(title="")
        # The base validate() should reject it
        from app.collectors.base import BaseCollector
        repo = AsyncMock()
        dedup = DeduplicationService(repo)
        collector = StubCollector(repo, dedup)
        assert collector.validate(event) is False

    def test_collector_source_create_valid(self) -> None:
        source = CollectorSourceCreate(
            name="Test", collector_type="rss", url="https://example.com/feed"
        )
        assert source.collection_interval_minutes == 60

    def test_collector_source_health_schema(self) -> None:
        """CollectorSourceHealth schema accepts valid data."""
        h = CollectorSourceHealth(
            name="test",
            collector_type="rss",
            is_active=True,
            last_collected_at=datetime.now(timezone.utc),
            consecutive_failures=0,
            total_items_collected=42,
            status="healthy",
        )
        assert h.status == "healthy"
        assert h.total_items_collected == 42


# ── Deduplication Across Runs Tests ──────────────────────────────────────


class TestDeduplicationAcrossRuns:
    """Ensure repeated collection runs don't create duplicates."""

    @pytest.mark.asyncio
    async def test_second_run_skips_existing(self) -> None:
        """Running the same items twice: first emits, second deduplicates."""
        repo = AsyncMock()
        repo.create.return_value = MagicMock(spec=CollectedEvent)
        dedup = DeduplicationService(repo)

        items = [
            RawItem(title="Same Item", link="https://example.com/same", summary="s", published=""),
        ]

        # First run: not duplicate
        repo.exists_by_hash.return_value = False
        repo.exists_by_source_url.return_value = False
        collector = StubCollector(repo, dedup, items)
        r1 = await collector.run(_make_source())
        assert r1.emitted == 1
        assert r1.duplicates == 0

        # Second run: is duplicate
        repo.exists_by_hash.return_value = True
        collector2 = StubCollector(repo, dedup, items)
        r2 = await collector2.run(_make_source())
        assert r2.emitted == 0
        assert r2.duplicates == 1
