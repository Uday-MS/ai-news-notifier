"""Feed repository — read-only data access for the Intelligence Feed.

Provides composable query building over ProcessedEvent joined with
CollectedEvent. All filter logic lives in _apply_filters() to avoid
SQL duplication between search and count queries.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Select, String, case, cast, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import CollectedEvent
from app.models.processed_event import AICategory, ProcessedEvent, ProcessingStatus


class FeedRepository:
    """Read-only repository for feed queries over processed + collected events."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Core query builder ───────────────────────────────────────────────

    def _base_query(self) -> Select:
        """Build the base SELECT joining ProcessedEvent with CollectedEvent."""
        return (
            select(
                ProcessedEvent,
                CollectedEvent.source,
                CollectedEvent.source_url,
                CollectedEvent.organization,
                CollectedEvent.published_at,
            )
            .join(
                CollectedEvent,
                ProcessedEvent.collected_event_id == CollectedEvent.id,
            )
            .where(ProcessedEvent.processing_status == ProcessingStatus.READY)
        )

    def _apply_filters(
        self,
        stmt: Select,
        *,
        keyword: str | None = None,
        category: str | None = None,
        source: str | None = None,
        tag: str | None = None,
        importance_min: int | None = None,
        importance_max: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        status: str | None = None,
    ) -> Select:
        """Apply all optional filters to a statement. Shared by search + count."""
        if keyword:
            pattern = f"%{keyword}%"
            stmt = stmt.where(
                ProcessedEvent.cleaned_title.ilike(pattern)
                | ProcessedEvent.cleaned_summary.ilike(pattern)
            )

        if category:
            stmt = stmt.where(ProcessedEvent.ai_category == category)

        if source:
            stmt = stmt.where(CollectedEvent.source.ilike(f"%{source}%"))

        if tag:
            # SQLite JSON: use LIKE on the JSON column for portability
            stmt = stmt.where(
                cast(ProcessedEvent.ai_tags, String).ilike(f"%{tag}%")
            )

        if importance_min is not None:
            stmt = stmt.where(ProcessedEvent.importance_score >= importance_min)

        if importance_max is not None:
            stmt = stmt.where(ProcessedEvent.importance_score <= importance_max)

        if date_from:
            stmt = stmt.where(CollectedEvent.published_at >= date_from)

        if date_to:
            stmt = stmt.where(CollectedEvent.published_at <= date_to)

        if status:
            stmt = stmt.where(ProcessedEvent.processing_status == status)

        return stmt

    def _apply_sort(self, stmt: Select, sort: str = "newest") -> Select:
        """Apply sorting to a statement."""
        if sort == "oldest":
            return stmt.order_by(CollectedEvent.published_at.asc())
        elif sort == "highest_importance":
            return stmt.order_by(
                ProcessedEvent.importance_score.desc(),
                CollectedEvent.published_at.desc(),
            )
        else:  # newest (default)
            return stmt.order_by(CollectedEvent.published_at.desc())

    # ── Search ───────────────────────────────────────────────────────────

    async def search(
        self,
        *,
        keyword: str | None = None,
        category: str | None = None,
        source: str | None = None,
        tag: str | None = None,
        importance_min: int | None = None,
        importance_max: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sort: str = "newest",
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Search processed events with composable filters.

        Returns dicts with ProcessedEvent fields + joined CollectedEvent fields.
        """
        stmt = self._base_query()
        stmt = self._apply_filters(
            stmt,
            keyword=keyword,
            category=category,
            source=source,
            tag=tag,
            importance_min=importance_min,
            importance_max=importance_max,
            date_from=date_from,
            date_to=date_to,
        )
        stmt = self._apply_sort(stmt, sort)
        stmt = stmt.limit(limit).offset(offset)

        result = await self._db.execute(stmt)
        rows = result.all()
        return [self._row_to_dict(row) for row in rows]

    async def count_filtered(
        self,
        *,
        keyword: str | None = None,
        category: str | None = None,
        source: str | None = None,
        tag: str | None = None,
        importance_min: int | None = None,
        importance_max: int | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> int:
        """Count events matching the given filters."""
        stmt = (
            select(func.count())
            .select_from(ProcessedEvent)
            .join(
                CollectedEvent,
                ProcessedEvent.collected_event_id == CollectedEvent.id,
            )
            .where(ProcessedEvent.processing_status == ProcessingStatus.READY)
        )
        stmt = self._apply_filters(
            stmt,
            keyword=keyword,
            category=category,
            source=source,
            tag=tag,
            importance_min=importance_min,
            importance_max=importance_max,
            date_from=date_from,
            date_to=date_to,
        )
        result = await self._db.execute(stmt)
        return result.scalar() or 0

    # ── Single item ──────────────────────────────────────────────────────

    async def get_by_id(self, event_id: uuid.UUID) -> dict[str, Any] | None:
        """Fetch a single feed item by ProcessedEvent ID."""
        stmt = (
            self._base_query()
            .where(ProcessedEvent.id == event_id)
        )
        # Remove the READY filter for detail view (allow viewing PARTIAL too)
        # Actually, let's keep it — only expose READY items in the feed
        result = await self._db.execute(stmt)
        row = result.first()
        if row is None:
            return None
        return self._row_to_dict(row)

    # ── Aggregations ─────────────────────────────────────────────────────

    async def top_categories(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return categories ranked by event count."""
        stmt = (
            select(
                ProcessedEvent.ai_category,
                func.count().label("count"),
            )
            .where(ProcessedEvent.processing_status == ProcessingStatus.READY)
            .group_by(ProcessedEvent.ai_category)
            .order_by(func.count().desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return [
            {"category": row[0].value if hasattr(row[0], "value") else str(row[0]), "count": row[1]}
            for row in result.all()
        ]

    async def most_important(self, limit: int = 10) -> list[dict[str, Any]]:
        """Return the highest-importance READY events."""
        stmt = self._base_query()
        stmt = stmt.order_by(
            ProcessedEvent.importance_score.desc(),
            CollectedEvent.published_at.desc(),
        ).limit(limit)
        result = await self._db.execute(stmt)
        return [self._row_to_dict(row) for row in result.all()]

    async def top_tags(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return tags ranked by frequency across all READY events.

        Since ai_tags is a JSON array, we fetch all tag arrays and
        aggregate in Python for SQLite compatibility.
        """
        stmt = (
            select(ProcessedEvent.ai_tags)
            .where(ProcessedEvent.processing_status == ProcessingStatus.READY)
        )
        result = await self._db.execute(stmt)
        tag_counts: dict[str, int] = {}
        for (tags_json,) in result.all():
            if isinstance(tags_json, list):
                for tag in tags_json:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"tag": t, "count": c} for t, c in sorted_tags[:limit]]

    async def top_entities(self, limit: int = 20) -> list[dict[str, Any]]:
        """Return entities ranked by frequency across all READY events.

        Aggregates across all entity types from the JSON entities column.
        """
        stmt = (
            select(ProcessedEvent.entities)
            .where(ProcessedEvent.processing_status == ProcessingStatus.READY)
        )
        result = await self._db.execute(stmt)
        entity_counts: dict[tuple[str, str], int] = {}
        for (entities_json,) in result.all():
            if isinstance(entities_json, dict):
                for entity_type, entity_list in entities_json.items():
                    if isinstance(entity_list, list):
                        for entity in entity_list:
                            key = (str(entity), entity_type)
                            entity_counts[key] = entity_counts.get(key, 0) + 1
        sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {"entity": e, "entity_type": t, "count": c}
            for (e, t), c in sorted_entities[:limit]
        ]

    async def count_ready(self) -> int:
        """Count total READY processed events."""
        result = await self._db.execute(
            select(func.count())
            .select_from(ProcessedEvent)
            .where(ProcessedEvent.processing_status == ProcessingStatus.READY)
        )
        return result.scalar() or 0

    # ── Helpers ──────────────────────────────────────────────────────────

    def _row_to_dict(self, row) -> dict[str, Any]:
        """Convert a joined query row to a dict suitable for schema validation."""
        pe: ProcessedEvent = row[0]
        return {
            "id": pe.id,
            "collected_event_id": pe.collected_event_id,
            "cleaned_title": pe.cleaned_title,
            "cleaned_summary": pe.cleaned_summary,
            "ai_summary": pe.ai_summary,
            "ai_category": pe.ai_category,
            "ai_tags": pe.ai_tags,
            "entities": pe.entities,
            "importance_score": pe.importance_score,
            "importance_reason": pe.importance_reason,
            "processing_status": pe.processing_status,
            "processed_at": pe.processed_at,
            "created_at": pe.created_at,
            # Joined from CollectedEvent
            "source": row[1],
            "source_url": row[2],
            "organization": row[3],
            "published_at": row[4],
        }
