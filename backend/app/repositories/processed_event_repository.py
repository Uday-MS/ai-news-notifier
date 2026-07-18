"""Repository for ProcessedEvent — data access layer."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processed_event import ProcessedEvent, ProcessingStatus


class ProcessedEventRepository:
    """Handles all database operations for ProcessedEvent."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, **kwargs: Any) -> ProcessedEvent:
        """Persist a new processed event and return it."""
        event = ProcessedEvent(**kwargs)
        self._db.add(event)
        await self._db.flush()
        await self._db.refresh(event)
        return event

    async def update(self, event_id: uuid.UUID, **kwargs: Any) -> ProcessedEvent | None:
        """Update fields on an existing processed event."""
        event = await self.get_by_id(event_id)
        if event is None:
            return None
        for key, value in kwargs.items():
            setattr(event, key, value)
        await self._db.flush()
        await self._db.refresh(event)
        return event

    async def get_by_id(self, event_id: uuid.UUID) -> ProcessedEvent | None:
        result = await self._db.execute(
            select(ProcessedEvent).where(ProcessedEvent.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_by_collected_event_id(
        self, collected_event_id: uuid.UUID
    ) -> ProcessedEvent | None:
        result = await self._db.execute(
            select(ProcessedEvent).where(
                ProcessedEvent.collected_event_id == collected_event_id
            )
        )
        return result.scalar_one_or_none()

    async def list_events(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[ProcessedEvent]:
        """Return a paginated list of processed events."""
        stmt = select(ProcessedEvent).order_by(
            ProcessedEvent.processed_at.desc().nullslast()
        )
        if status:
            stmt = stmt.where(ProcessedEvent.processing_status == status)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count_by_status(self) -> dict[str, int]:
        """Return counts grouped by processing status."""
        stmt = (
            select(
                ProcessedEvent.processing_status,
                func.count().label("count"),
            )
            .group_by(ProcessedEvent.processing_status)
        )
        result = await self._db.execute(stmt)
        counts: dict[str, int] = {}
        for row in result.all():
            counts[row[0].value if hasattr(row[0], "value") else str(row[0])] = row[1]
        return counts

    async def count_total(self) -> int:
        """Return total number of processed events."""
        result = await self._db.execute(
            select(func.count()).select_from(ProcessedEvent)
        )
        return result.scalar() or 0
