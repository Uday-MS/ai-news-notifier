"""Abstract base collector — defines the fetch/normalize/validate/emit interface."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TypedDict

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.models.collector_source import CollectorSource
from app.models.event import CollectedEvent
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventCreate
from app.services.dedup_service import DeduplicationService


# ── Exceptions that warrant a retry ──────────────────────────────────────

_RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    ConnectionError,
    TimeoutError,
)


class RawItem(TypedDict, total=False):
    """Unstructured item as received from a data source."""

    title: str
    summary: str
    link: str
    published: str
    author: str
    tags: list[str]
    extra: dict[str, Any]


@dataclass
class CollectorRunResult:
    """Summary statistics for a single collector run."""

    collector_type: str
    source_name: str
    fetched: int = 0
    normalised: int = 0
    validated: int = 0
    emitted: int = 0
    duplicates: int = 0
    errors: int = 0
    error_messages: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None


class BaseCollector(ABC):
    """Abstract collector that every concrete collector must implement.

    The ``run()`` method orchestrates the pipeline:
    ``fetch → normalize → validate → emit`` with structured logging,
    per-item error isolation, and bounded retry on transient failures.
    """

    collector_type: str = "base"

    def __init__(
        self,
        event_repo: EventRepository,
        dedup_service: DeduplicationService,
    ) -> None:
        self._event_repo = event_repo
        self._dedup = dedup_service
        self._log = get_logger(f"collector.{self.collector_type}")

    # ── Abstract methods (must override) ─────────────────────────────────

    @abstractmethod
    async def fetch(self, source: CollectorSource) -> list[RawItem]:
        """Retrieve raw items from the external source."""

    @abstractmethod
    def normalize(self, raw: RawItem, source: CollectorSource) -> EventCreate:
        """Transform a raw item into a normalised EventCreate schema."""

    # ── Overridable defaults ─────────────────────────────────────────────

    def validate(self, event: EventCreate) -> bool:
        """Return True if the event passes quality checks.

        Default implementation checks that required fields are non-empty.
        Override for source-specific validation.
        """
        return bool(
            event.title.strip()
            and event.source_url.strip()
            and event.summary.strip()
        )

    async def emit(self, event: EventCreate) -> CollectedEvent | None:
        """Persist the event if it is not a duplicate. Returns the saved
        model instance, or *None* if it was deduplicated.

        Also catches database IntegrityError (e.g. duplicate source_url)
        and treats it as a dedup hit to avoid corrupting the session.
        """
        if await self._dedup.is_duplicate(event):
            return None

        try:
            return await self._event_repo.create(**event.model_dump())
        except Exception as exc:
            # Handle unique constraint violations gracefully
            exc_str = str(exc).lower()
            if "unique" in exc_str or "integrity" in exc_str or "duplicate" in exc_str:
                # Rollback the failed flush so the session remains usable
                await self._event_repo._db.rollback()
                self._log.debug(
                    "Duplicate caught by DB constraint",
                    extra={"context": {"title": event.title, "url": event.source_url}},
                )
                return None
            raise

    # ── Fetch with retry ─────────────────────────────────────────────────

    async def _fetch_with_retry(self, source: CollectorSource) -> list[RawItem]:
        """Fetch with bounded exponential backoff on transient errors.

        Retries up to ``COLLECTOR_MAX_RETRIES`` times (default 3) on
        network timeouts, connection errors, and 5xx HTTP responses.
        Non-retryable errors (4xx, parse errors) fail immediately.
        """
        max_retries = settings.COLLECTOR_MAX_RETRIES
        backoff_base = settings.COLLECTOR_RETRY_BACKOFF_BASE
        last_exc: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                return await self.fetch(source)
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500:
                    last_exc = exc
                    if attempt < max_retries:
                        wait = backoff_base * (2 ** attempt)
                        self._log.warning(
                            f"Fetch returned {exc.response.status_code}, retry {attempt + 1}/{max_retries} in {wait}s",
                            extra={"context": {"source": source.name}},
                        )
                        await asyncio.sleep(wait)
                        continue
                # 4xx — don't retry
                raise
            except _RETRYABLE_EXCEPTIONS as exc:
                last_exc = exc
                if attempt < max_retries:
                    wait = backoff_base * (2 ** attempt)
                    self._log.warning(
                        f"Fetch transient error ({type(exc).__name__}), retry {attempt + 1}/{max_retries} in {wait}s",
                        extra={"context": {"source": source.name}},
                    )
                    await asyncio.sleep(wait)
                    continue
                raise

        # Should not reach here, but just in case
        if last_exc:
            raise last_exc
        return []

    # ── Pipeline orchestrator ────────────────────────────────────────────

    async def run(self, source: CollectorSource) -> CollectorRunResult:
        """Execute the full collection pipeline for *source*."""
        result = CollectorRunResult(
            collector_type=self.collector_type,
            source_name=source.name,
        )

        self._log.info(
            "Collector run started",
            extra={"context": {"source": source.name, "url": source.url}},
        )

        # 1. Fetch (with retry)
        try:
            raw_items = await self._fetch_with_retry(source)
            result.fetched = len(raw_items)
        except Exception as exc:
            result.errors += 1
            result.error_messages.append(f"Fetch failed: {exc}")
            self._log.error(
                "Fetch failed",
                exc_info=exc,
                extra={"context": {"source": source.name}},
            )
            result.finished_at = datetime.now(timezone.utc)
            return result

        # 2–4. Normalize → Validate → Emit (per item)
        for raw in raw_items:
            try:
                event = self.normalize(raw, source)
                result.normalised += 1
            except Exception as exc:
                result.errors += 1
                result.error_messages.append(
                    f"Normalize error: {exc} | raw_title={raw.get('title', '?')}"
                )
                continue

            if not self.validate(event):
                result.errors += 1
                result.error_messages.append(
                    f"Validation failed: {event.title}"
                )
                continue
            result.validated += 1

            try:
                saved = await self.emit(event)
                if saved is None:
                    result.duplicates += 1
                else:
                    result.emitted += 1
            except Exception as exc:
                result.errors += 1
                result.error_messages.append(f"Emit error: {exc}")

        result.finished_at = datetime.now(timezone.utc)
        self._log.info(
            "Collector run finished",
            extra={
                "context": {
                    "source": source.name,
                    "fetched": result.fetched,
                    "emitted": result.emitted,
                    "duplicates": result.duplicates,
                    "errors": result.errors,
                }
            },
        )
        return result
