"""Collector orchestration service."""

from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.base import CollectorRunResult
from app.collectors.registry import collector_registry
from app.core.logging import get_logger
from app.repositories.collector_source_repository import CollectorSourceRepository
from app.repositories.event_repository import EventRepository
from app.services.dedup_service import DeduplicationService

logger = get_logger("collector.service")


class CollectorService:
    """High-level service that wires sources to collectors and runs them."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._source_repo = CollectorSourceRepository(db)
        self._event_repo = EventRepository(db)
        self._dedup = DeduplicationService(self._event_repo)

    async def run_collector(self, source_id: uuid.UUID) -> CollectorRunResult:
        """Run the collector for a single registered source."""
        source = await self._source_repo.get_by_id(source_id)
        if source is None:
            raise ValueError(f"Collector source {source_id} not found.")

        collector_cls = collector_registry.get(source.collector_type)
        if collector_cls is None:
            raise ValueError(
                f"No collector registered for type '{source.collector_type}'."
            )

        collector = collector_cls(
            event_repo=self._event_repo,
            dedup_service=self._dedup,
        )
        result = await collector.run(source)

        # Update last_collected_at timestamp
        await self._source_repo.update_last_collected(
            source.id, datetime.now(timezone.utc)
        )

        return result

    async def run_all_active(self) -> list[dict]:
        """Run collectors for every active source and return summaries."""
        sources = await self._source_repo.get_active_sources()
        results: list[dict] = []

        for source in sources:
            try:
                result = await self.run_collector(source.id)
                results.append(asdict(result))
            except Exception as exc:
                logger.error(
                    "Failed to run collector for source",
                    exc_info=exc,
                    extra={"context": {"source": source.name}},
                )
                results.append(
                    {
                        "collector_type": source.collector_type,
                        "source_name": source.name,
                        "errors": 1,
                        "error_messages": [str(exc)],
                    }
                )

        return results
