"""Repository for ProcessingLog — data access layer."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.processing_log import ProcessingLog


class ProcessingLogRepository:
    """Handles all database operations for ProcessingLog."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, **kwargs: Any) -> ProcessingLog:
        """Persist a new processing log entry."""
        log = ProcessingLog(**kwargs)
        self._db.add(log)
        await self._db.flush()
        await self._db.refresh(log)
        return log

    async def get_logs_for_event(
        self, processed_event_id: uuid.UUID
    ) -> list[ProcessingLog]:
        """Return all log entries for a given processed event."""
        stmt = (
            select(ProcessingLog)
            .where(ProcessingLog.processed_event_id == processed_event_id)
            .order_by(ProcessingLog.created_at.asc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
