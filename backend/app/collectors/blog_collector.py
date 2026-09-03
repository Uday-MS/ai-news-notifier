"""Official blog feed collector — specialised RSS for AI org blogs."""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from app.collectors.base import BaseCollector, RawItem
from app.core.config import settings
from app.models.collector_source import CollectorSource
from app.models.event import EventType
from app.schemas.event import EventCreate
from app.services.dedup_service import DeduplicationService


class BlogCollector(BaseCollector):
    """Collects posts from official AI organisation blog feeds.

    Similar to ``RSSCollector`` but with blog-specific normalisation:
    - Default event type is ``BLOG_POST``
    - Extracts author into metadata
    - Maps feed categories to tags
    """

    collector_type: str = "blog"

    async def fetch(self, source: CollectorSource) -> list[RawItem]:
        """Download and parse the blog feed."""
        async with httpx.AsyncClient(
            timeout=settings.COLLECTOR_REQUEST_TIMEOUT,
            follow_redirects=True,
        ) as client:
            response = await client.get(source.url)
            response.raise_for_status()

        feed = feedparser.parse(response.text)
        items: list[RawItem] = []

        for entry in feed.entries[: settings.COLLECTOR_MAX_ITEMS_PER_RUN]:
            # Prefer content:encoded over summary for blog posts
            content = ""
            if entry.get("content"):
                content = entry["content"][0].get("value", "")
            if not content:
                content = entry.get("summary", entry.get("description", ""))
            # Fallback: use title when no summary/content is available
            if not content.strip():
                content = entry.get("title", "No description available.")

            items.append(
                RawItem(
                    title=entry.get("title", ""),
                    summary=content,
                    link=entry.get("link", ""),
                    published=entry.get("published", entry.get("updated", "")),
                    author=entry.get("author", ""),
                    tags=[
                        tag.get("term", "") for tag in entry.get("tags", [])
                    ],
                    extra={
                        "feed_title": feed.feed.get("title", ""),
                        "entry_id": entry.get("id", ""),
                        "author": entry.get("author", ""),
                    },
                )
            )
        return items

    def normalize(self, raw: RawItem, source: CollectorSource) -> EventCreate:
        """Convert a blog post entry into a normalised EventCreate."""
        published_at = self._parse_date(raw.get("published", ""))
        source_url = raw.get("link", "")
        title = raw.get("title", "Untitled")

        content_hash = DeduplicationService.generate_content_hash(
            source_url, title, published_at
        )

        organization = (
            source.config.get("organization")
            or raw.get("extra", {}).get("feed_title", "")
            or source.name
        )

        # Strip HTML tags from summary for clean plaintext
        summary = raw.get("summary", "")
        if len(summary) > 2000:
            summary = summary[:1997] + "..."

        return EventCreate(
            title=title,
            summary=summary,
            source=source.name,
            source_url=source_url,
            published_at=published_at,
            event_type=EventType(
                source.config.get("event_type", EventType.BLOG_POST.value)
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
        """Best-effort date parsing for blog feed date formats."""
        if not date_str:
            return datetime.now(timezone.utc)
        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            pass
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)
