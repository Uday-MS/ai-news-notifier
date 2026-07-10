"""Deduplication service — prevents duplicate events in the pipeline."""

from __future__ import annotations

import hashlib
from datetime import datetime

from app.repositories.event_repository import EventRepository
from app.schemas.event import EventCreate


class DeduplicationService:
    """Content-hash based deduplication for collected events.

    The hash is derived from ``(source_url, title, published_at)`` so that
    the same article from the same source is never stored twice, even if
    minor metadata differences exist between runs.
    """

    def __init__(self, event_repo: EventRepository) -> None:
        self._event_repo = event_repo

    @staticmethod
    def generate_content_hash(
        source_url: str,
        title: str,
        published_at: datetime,
    ) -> str:
        """Produce a deterministic SHA-256 hex digest for dedup purposes."""
        raw = f"{source_url.strip().lower()}|{title.strip().lower()}|{published_at.isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def is_duplicate(self, event: EventCreate) -> bool:
        """Check whether an event with the same content hash exists."""
        return await self._event_repo.exists_by_hash(event.content_hash)
