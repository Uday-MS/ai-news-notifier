"""CollectorSource repository — data access layer for registered sources."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collector_source import CollectorSource


class CollectorSourceRepository:
    """Handles all database operations for CollectorSource."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, **kwargs: Any) -> CollectorSource:
        source = CollectorSource(**kwargs)
        self._db.add(source)
        await self._db.flush()
        await self._db.refresh(source)
        return source

    async def get_by_id(self, source_id: uuid.UUID) -> CollectorSource | None:
        result = await self._db.execute(
            select(CollectorSource).where(CollectorSource.id == source_id)
        )
        return result.scalar_one_or_none()

    async def get_active_sources(
        self, collector_type: str | None = None
    ) -> list[CollectorSource]:
        """Return all active sources, optionally filtered by collector type."""
        stmt = select(CollectorSource).where(CollectorSource.is_active.is_(True))
        if collector_type:
            stmt = stmt.where(CollectorSource.collector_type == collector_type)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_due_sources(self, now: datetime) -> list[CollectorSource]:
        """Return active sources whose collection interval has elapsed.

        A source is 'due' if it has never been collected, or if
        ``now - last_collected_at >= collection_interval_minutes``.
        """
        stmt = select(CollectorSource).where(CollectorSource.is_active.is_(True))
        result = await self._db.execute(stmt)
        sources = list(result.scalars().all())

        due: list[CollectorSource] = []
        for src in sources:
            if src.last_collected_at is None:
                due.append(src)
            else:
                # Ensure timezone-aware comparison (SQLite stores naive datetimes)
                last = src.last_collected_at
                if last.tzinfo is None:
                    from datetime import timezone
                    last = last.replace(tzinfo=timezone.utc)
                elapsed = (now - last).total_seconds() / 60
                if elapsed >= src.collection_interval_minutes:
                    due.append(src)
        return due

    async def list_all(self) -> list[CollectorSource]:
        result = await self._db.execute(
            select(CollectorSource).order_by(CollectorSource.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_last_collected(
        self, source_id: uuid.UUID, timestamp: datetime
    ) -> None:
        """Mark a source as last collected at the given time."""
        await self._db.execute(
            update(CollectorSource)
            .where(CollectorSource.id == source_id)
            .values(last_collected_at=timestamp)
        )
        await self._db.flush()

    async def record_success(
        self, source_id: uuid.UUID, timestamp: datetime, items_collected: int
    ) -> None:
        """Record a successful collection run — clears error state."""
        await self._db.execute(
            update(CollectorSource)
            .where(CollectorSource.id == source_id)
            .values(
                last_collected_at=timestamp,
                last_error=None,
                last_error_at=None,
                consecutive_failures=0,
                total_items_collected=CollectorSource.total_items_collected + items_collected,
            )
        )
        await self._db.flush()

    async def record_failure(
        self, source_id: uuid.UUID, timestamp: datetime, error_message: str
    ) -> None:
        """Record a failed collection run — increments failure counter."""
        await self._db.execute(
            update(CollectorSource)
            .where(CollectorSource.id == source_id)
            .values(
                last_error=error_message[:2000],  # truncate to avoid overflow
                last_error_at=timestamp,
                consecutive_failures=CollectorSource.consecutive_failures + 1,
            )
        )
        await self._db.flush()

    async def update(self, source_id: uuid.UUID, **kwargs: Any) -> CollectorSource | None:
        await self._db.execute(
            update(CollectorSource)
            .where(CollectorSource.id == source_id)
            .values(**kwargs)
        )
        await self._db.flush()
        return await self.get_by_id(source_id)
