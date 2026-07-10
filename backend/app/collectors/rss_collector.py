"""RSS/Atom feed collector using feedparser + httpx."""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import httpx

from app.collectors.base import BaseCollector, RawItem
from app.core.config import settings
from app.models.collector_source import CollectorSource
from app.schemas.event import EventCreate
from app.models.event import EventType
from app.services.dedup_service import DeduplicationService


class RSSCollector(BaseCollector):
    """Collects events from RSS and Atom feeds.

    Uses ``httpx`` for fetching and ``feedparser`` for parsing so that
    we can set timeouts and custom headers without blocking the event loop.
    """

    collector_type: str = "rss"

    async def fetch(self, source: CollectorSource) -> list[RawItem]:
        """Download and parse the RSS/Atom feed, returning raw entries."""
        async with httpx.AsyncClient(
            timeout=settings.COLLECTOR_REQUEST_TIMEOUT
        ) as client:
            response = await client.get(source.url)
            response.raise_for_status()

        feed = feedparser.parse(response.text)
        items: list[RawItem] = []

        for entry in feed.entries[: settings.COLLECTOR_MAX_ITEMS_PER_RUN]:
            items.append(
                RawItem(
                    title=entry.get("title", ""),
                    summary=entry.get("summary", entry.get("description", "")),
                    link=entry.get("link", ""),
                    published=entry.get("published", entry.get("updated", "")),
                    author=entry.get("author", ""),
                    tags=[
                        tag.get("term", "") for tag in entry.get("tags", [])
                    ],
                    extra={
                        "feed_title": feed.feed.get("title", ""),
                        "entry_id": entry.get("id", ""),
                    },
                )
            )
        return items

    def normalize(self, raw: RawItem, source: CollectorSource) -> EventCreate:
        """Convert a raw RSS entry into a normalised EventCreate."""
        published_at = self._parse_date(raw.get("published", ""))
        source_url = raw.get("link", "")
        title = raw.get("title", "Untitled")

        content_hash = DeduplicationService.generate_content_hash(
            source_url, title, published_at
        )

        # Determine organization from source config or feed title
        organization = (
            source.config.get("organization")
            or raw.get("extra", {}).get("feed_title", "")
            or source.name
        )

        return EventCreate(
            title=title,
            summary=raw.get("summary", ""),
            source=source.name,
            source_url=source_url,
            published_at=published_at,
            event_type=EventType(
                source.config.get("event_type", EventType.NEWS.value)
            ),
            organization=organization,
            tags=raw.get("tags", []),
            extra_metadata=raw.get("extra", {}),
            collector_id=self.collector_type,
            content_hash=content_hash,
        )

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Best-effort date parsing for RSS date formats."""
        if not date_str:
            return datetime.now(timezone.utc)
        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            pass
        # feedparser sometimes gives a time struct
        try:
            import time
            return datetime(*feedparser._parse_date(date_str)[:6], tzinfo=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)
