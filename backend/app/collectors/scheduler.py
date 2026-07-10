"""Scheduler interface for collector execution.

Provides an abstract ``CollectorScheduler`` and a ``ManualScheduler``
stub for Sprint 3.  Production scheduling (Celery / APScheduler) will
implement the same interface in a future sprint.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod


class CollectorScheduler(ABC):
    """Abstract scheduler that future integrations must implement."""

    @abstractmethod
    async def start(self) -> None:
        """Start the scheduling loop."""

    @abstractmethod
    async def stop(self) -> None:
        """Gracefully stop the scheduler."""

    @abstractmethod
    async def trigger(self, source_id: uuid.UUID) -> None:
        """Immediately trigger collection for a specific source."""

    @abstractmethod
    async def schedule_source(
        self, source_id: uuid.UUID, interval_minutes: int
    ) -> None:
        """Register a source for periodic collection."""

    @abstractmethod
    async def unschedule_source(self, source_id: uuid.UUID) -> None:
        """Remove a source from the schedule."""


class ManualScheduler(CollectorScheduler):
    """No-op scheduler for Sprint 3.

    Collectors are triggered manually via the API.  This class satisfies
    the interface contract so that the rest of the codebase can depend on
    ``CollectorScheduler`` without coupling to a specific backend.
    """

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def trigger(self, source_id: uuid.UUID) -> None:
        # In Sprint 3, triggering is handled directly by CollectorService
        pass

    async def schedule_source(
        self, source_id: uuid.UUID, interval_minutes: int
    ) -> None:
        pass

    async def unschedule_source(self, source_id: uuid.UUID) -> None:
        pass
