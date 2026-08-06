"""Saved Article repository — data access for bookmarks."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.saved_article import SavedArticle
from app.models.processed_event import ProcessedEvent, ProcessingStatus
from app.models.event import CollectedEvent


class SavedArticleRepository:
    """CRUD operations for saved articles."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def save(self, user_id: uuid.UUID, event_id: uuid.UUID) -> SavedArticle:
        """Save an article. Returns existing if already saved."""
        existing = await self._get(user_id, event_id)
        if existing:
            return existing
        saved = SavedArticle(user_id=user_id, processed_event_id=event_id)
        self._db.add(saved)
        await self._db.flush()
        return saved

    async def unsave(self, user_id: uuid.UUID, event_id: uuid.UUID) -> bool:
        """Remove a saved article. Returns True if deleted."""
        result = await self._db.execute(
            delete(SavedArticle).where(
                SavedArticle.user_id == user_id,
                SavedArticle.processed_event_id == event_id,
            )
        )
        await self._db.flush()
        return result.rowcount > 0  # type: ignore[union-attr]

    async def get_saved(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        """Return the user's saved articles as dicts (joined with CollectedEvent), plus total count."""
        # Count
        count_q = select(func.count()).select_from(SavedArticle).where(
            SavedArticle.user_id == user_id
        )
        total = (await self._db.execute(count_q)).scalar() or 0

        # Items — join SavedArticle → ProcessedEvent → CollectedEvent
        items_q = (
            select(
                ProcessedEvent,
                CollectedEvent.source,
                CollectedEvent.source_url,
                CollectedEvent.organization,
                CollectedEvent.published_at,
            )
            .join(SavedArticle, SavedArticle.processed_event_id == ProcessedEvent.id)
            .join(CollectedEvent, ProcessedEvent.collected_event_id == CollectedEvent.id)
            .where(
                SavedArticle.user_id == user_id,
                ProcessedEvent.processing_status == ProcessingStatus.READY,
            )
            .order_by(SavedArticle.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._db.execute(items_q)
        rows = result.all()

        items = []
        for row in rows:
            pe: ProcessedEvent = row[0]
            items.append({
                "id": pe.id,
                "collected_event_id": pe.collected_event_id,
                "cleaned_title": pe.cleaned_title,
                "ai_summary": pe.ai_summary,
                "ai_category": pe.ai_category,
                "ai_tags": pe.ai_tags,
                "importance_score": pe.importance_score,
                "processed_at": pe.processed_at,
                "source": row[1],
                "source_url": row[2],
                "organization": row[3],
                "published_at": row[4],
            })
        return items, total

    async def is_saved(self, user_id: uuid.UUID, event_id: uuid.UUID) -> bool:
        """Check if a specific article is saved."""
        existing = await self._get(user_id, event_id)
        return existing is not None

    async def count(self, user_id: uuid.UUID) -> int:
        """Count total saved articles for a user."""
        q = select(func.count()).select_from(SavedArticle).where(
            SavedArticle.user_id == user_id
        )
        return (await self._db.execute(q)).scalar() or 0

    async def _get(
        self, user_id: uuid.UUID, event_id: uuid.UUID
    ) -> SavedArticle | None:
        result = await self._db.execute(
            select(SavedArticle).where(
                SavedArticle.user_id == user_id,
                SavedArticle.processed_event_id == event_id,
            )
        )
        return result.scalar_one_or_none()
