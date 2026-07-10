"""Unit tests for the Collector Engine foundation (Sprint 3).

Tests cover:
- Deduplication service (hash generation, duplicate detection)
- Base collector pipeline logic
- Collector registry
- Event and source schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.collectors.base import BaseCollector, CollectorRunResult, RawItem
from app.collectors.registry import CollectorRegistry
from app.models.collector_source import CollectorSource
from app.models.event import CollectedEvent, EventType
from app.schemas.collector_source import CollectorSourceCreate
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
        repo.create.return_value = MagicMock(spec=CollectedEvent)
        dedup = DeduplicationService(repo)

        collector = StubCollector(repo, dedup, [])
        result = await collector.run(_make_source())

        assert result.started_at is not None
        assert result.finished_at is not None
        assert result.finished_at >= result.started_at


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
