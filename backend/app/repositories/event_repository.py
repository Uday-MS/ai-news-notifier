"""Event repository — data access layer for the CollectedEvent model."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import CollectedEvent


class EventRepository:
    """Handles all database operations for CollectedEvent."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, **kwargs: Any) -> CollectedEvent:
        """Persist a new event and return it."""
        event = CollectedEvent(**kwargs)
        self._db.add(event)
        await self._db.flush()
        await self._db.refresh(event)
        return event

    async def get_by_id(self, event_id: uuid.UUID) -> CollectedEvent | None:
        result = await self._db.execute(
            select(CollectedEvent).where(CollectedEvent.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_by_content_hash(self, content_hash: str) -> CollectedEvent | None:
        result = await self._db.execute(
            select(CollectedEvent).where(CollectedEvent.content_hash == content_hash)
        )
        return result.scalar_one_or_none()

    async def get_by_source_url(self, source_url: str) -> CollectedEvent | None:
        result = await self._db.execute(
            select(CollectedEvent).where(CollectedEvent.source_url == source_url)
        )
        return result.scalar_one_or_none()

    async def exists_by_hash(self, content_hash: str) -> bool:
        """Return True if an event with the given hash already exists."""
        result = await self._db.execute(
            select(func.count()).select_from(CollectedEvent).where(
                CollectedEvent.content_hash == content_hash
            )
        )
        return (result.scalar() or 0) > 0

    async def list_events(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        source: str | None = None,
        event_type: str | None = None,
    ) -> list[CollectedEvent]:
        """Return a paginated list of events, optionally filtered."""
        stmt = select(CollectedEvent).order_by(CollectedEvent.published_at.desc())

        if source:
            stmt = stmt.where(CollectedEvent.source == source)
        if event_type:
            stmt = stmt.where(CollectedEvent.event_type == event_type)

        stmt = stmt.limit(limit).offset(offset)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count_events(
        self,
        *,
        source: str | None = None,
        event_type: str | None = None,
    ) -> int:
        """Return total event count with optional filters."""
        stmt = select(func.count()).select_from(CollectedEvent)

        if source:
            stmt = stmt.where(CollectedEvent.source == source)
        if event_type:
            stmt = stmt.where(CollectedEvent.event_type == event_type)

        result = await self._db.execute(stmt)
        return result.scalar() or 0
