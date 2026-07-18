"""Pipeline Orchestrator Service.

Coordinates all seven processing stages for collected events, writes
ProcessedEvent and ProcessingLog records, and handles per-stage error
isolation.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.event import CollectedEvent
from app.models.processed_event import AICategory, ProcessedEvent, ProcessingStatus
from app.models.processing_log import StageStatus
from app.repositories.event_repository import EventRepository
from app.repositories.processed_event_repository import ProcessedEventRepository
from app.repositories.processing_log_repository import ProcessingLogRepository
from app.services.pipeline.cleaning_service import CleaningService
from app.services.pipeline.classification_service import ClassificationService
from app.services.pipeline.entity_service import EntityService
from app.services.pipeline.importance_service import ImportanceService
from app.services.pipeline.quality_service import QualityService
from app.services.pipeline.summary_service import BaseSummarizer, RuleBasedSummarizer
from app.services.pipeline.tag_service import TagService

logger = get_logger("pipeline.service")


@dataclass
class _StageLogEntry:
    """Collected log entry to be persisted after ProcessedEvent creation."""

    stage: str
    status: StageStatus
    duration_ms: int
    error_message: str | None = None
    stage_metadata: dict[str, Any] = field(default_factory=dict)


class PipelineService:
    """Orchestrates the AI processing pipeline for collected events."""

    def __init__(
        self,
        db: AsyncSession,
        summarizer: BaseSummarizer | None = None,
    ) -> None:
        self._db = db
        self._event_repo = EventRepository(db)
        self._processed_repo = ProcessedEventRepository(db)
        self._log_repo = ProcessingLogRepository(db)

        # Stage services (stateless)
        self._cleaner = CleaningService()
        self._classifier = ClassificationService()
        self._tagger = TagService()
        self._entity_extractor = EntityService()
        self._scorer = ImportanceService()
        self._summarizer: BaseSummarizer = summarizer or RuleBasedSummarizer()
        self._quality = QualityService()

    # ── Public API ───────────────────────────────────────────────────────

    async def process_single(self, event_id: uuid.UUID) -> ProcessedEvent:
        """Process a single collected event through all pipeline stages.

        Raises:
            ValueError: If the event is not found.
        """
        event = await self._event_repo.get_by_id(event_id)
        if event is None:
            raise ValueError(f"Collected event {event_id} not found.")

        # Check if already processed
        existing = await self._processed_repo.get_by_collected_event_id(event_id)
        if existing is not None:
            logger.info(
                "Event already processed, re-processing",
                extra={"context": {"event_id": str(event_id)}},
            )
            # Delete old processed event (cascade deletes logs)
            await self._db.delete(existing)
            await self._db.flush()

        return await self._run_pipeline(event)

    async def process_all_unprocessed(self) -> dict:
        """Process all collected events that haven't been processed yet.

        Returns:
            Summary dict with counts of processed, failed, skipped.
        """
        from sqlalchemy import select

        from app.models.processed_event import ProcessedEvent as PE

        subquery = select(PE.collected_event_id)
        stmt = (
            select(CollectedEvent)
            .where(CollectedEvent.id.notin_(subquery))
            .order_by(CollectedEvent.created_at.asc())
        )
        result = await self._db.execute(stmt)
        unprocessed = list(result.scalars().all())

        summary: dict[str, Any] = {
            "total": len(unprocessed),
            "processed": 0,
            "failed": 0,
            "results": [],
        }

        for event in unprocessed:
            try:
                processed = await self._run_pipeline(event)
                summary["processed"] += 1
                summary["results"].append({
                    "event_id": str(event.id),
                    "status": processed.processing_status.value,
                    "title": processed.cleaned_title,
                })
            except Exception as exc:
                summary["failed"] += 1
                summary["results"].append({
                    "event_id": str(event.id),
                    "status": "error",
                    "error": str(exc),
                })
                logger.error(
                    "Pipeline failed for event",
                    exc_info=exc,
                    extra={"context": {"event_id": str(event.id)}},
                )

        return summary

    # ── Pipeline execution ───────────────────────────────────────────────

    async def _run_pipeline(self, event: CollectedEvent) -> ProcessedEvent:
        """Execute all seven stages with per-stage error isolation.

        Strategy: collect all stage results and log entries first, then
        persist the ProcessedEvent, then write all logs with the correct FK.
        """
        stage_failures: list[str] = []
        log_entries: list[_StageLogEntry] = []

        # Initialize defaults
        cleaned_title = event.title
        cleaned_summary = event.summary
        ai_category = AICategory.OTHER
        ai_tags: list[str] = []
        entities: dict = {}
        importance_score = 0
        importance_reason = ""
        ai_summary = ""

        # ── Stage 1: Cleaning ────────────────────────────────────────────
        cleaned_title, cleaned_summary = self._run_stage(
            "cleaning", event, stage_failures, log_entries,
            lambda: self._stage_cleaning(event),
            default=(event.title, event.summary),
        )

        # ── Stage 2: Classification ──────────────────────────────────────
        ai_category = self._run_stage(
            "classification", event, stage_failures, log_entries,
            lambda: self._stage_classification(cleaned_title, cleaned_summary, event),
            default=AICategory.OTHER,
        )

        # ── Stage 3: Tag Extraction ──────────────────────────────────────
        ai_tags = self._run_stage(
            "tagging", event, stage_failures, log_entries,
            lambda: self._stage_tagging(cleaned_title, cleaned_summary, event),
            default=[],
        )

        # ── Stage 4: Entity Extraction ───────────────────────────────────
        entities = self._run_stage(
            "entity_extraction", event, stage_failures, log_entries,
            lambda: self._stage_entities(cleaned_title, cleaned_summary, event),
            default={},
        )

        # ── Stage 5: Importance Scoring ──────────────────────────────────
        importance_score, importance_reason = self._run_stage(
            "importance_scoring", event, stage_failures, log_entries,
            lambda: self._stage_importance(cleaned_title, cleaned_summary, event, ai_category),
            default=(0, ""),
        )

        # ── Stage 6: AI Summary ──────────────────────────────────────────
        ai_summary = await self._run_stage_async(
            "summarization", event, stage_failures, log_entries,
            lambda: self._stage_summary(cleaned_title, cleaned_summary, event, ai_category),
            default="",
        )

        # ── Stage 7: Quality Validation ──────────────────────────────────
        start = time.monotonic()
        quality_result = self._quality.validate(
            cleaned_title=cleaned_title,
            cleaned_summary=cleaned_summary,
            ai_category=ai_category,
            ai_tags=ai_tags,
            entities=entities,
            importance_score=importance_score,
            importance_reason=importance_reason,
            ai_summary=ai_summary,
            stage_failures=stage_failures,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        log_entries.append(_StageLogEntry(
            stage="quality_validation",
            status=StageStatus.SUCCESS,
            duration_ms=elapsed_ms,
            stage_metadata={
                "status": quality_result.status.value,
                "issues": quality_result.issues,
            },
        ))

        # ── Persist ProcessedEvent ───────────────────────────────────────
        processed = await self._processed_repo.create(
            collected_event_id=event.id,
            cleaned_title=cleaned_title,
            cleaned_summary=cleaned_summary,
            ai_category=ai_category,
            ai_tags=ai_tags,
            entities=entities,
            importance_score=importance_score,
            importance_reason=importance_reason,
            ai_summary=ai_summary,
            processing_status=quality_result.status,
            processed_at=datetime.now(timezone.utc),
        )

        # ── Persist all log entries with correct FK ──────────────────────
        for entry in log_entries:
            await self._log_repo.create(
                processed_event_id=processed.id,
                stage=entry.stage,
                status=entry.status,
                duration_ms=entry.duration_ms,
                error_message=entry.error_message,
                stage_metadata=entry.stage_metadata,
            )

        logger.info(
            "Pipeline completed",
            extra={
                "context": {
                    "event_id": str(event.id),
                    "processed_id": str(processed.id),
                    "status": quality_result.status.value,
                    "score": importance_score,
                    "category": ai_category.value,
                    "failures": stage_failures,
                }
            },
        )

        return processed

    # ── Stage runners ────────────────────────────────────────────────────

    def _run_stage(
        self,
        stage_name: str,
        event: CollectedEvent,
        stage_failures: list[str],
        log_entries: list[_StageLogEntry],
        fn,
        default,
    ):
        """Execute a synchronous stage function with timing and error isolation."""
        start = time.monotonic()
        try:
            result = fn()
            elapsed_ms = int((time.monotonic() - start) * 1000)
            log_entries.append(_StageLogEntry(
                stage=stage_name,
                status=StageStatus.SUCCESS,
                duration_ms=elapsed_ms,
                stage_metadata={"event_id": str(event.id)},
            ))
            return result
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            stage_failures.append(stage_name)
            log_entries.append(_StageLogEntry(
                stage=stage_name,
                status=StageStatus.FAILED,
                duration_ms=elapsed_ms,
                error_message=str(exc),
                stage_metadata={"event_id": str(event.id)},
            ))
            logger.warning(
                f"Pipeline stage '{stage_name}' failed",
                extra={"context": {"event_id": str(event.id), "error": str(exc)}},
            )
            return default

    async def _run_stage_async(
        self,
        stage_name: str,
        event: CollectedEvent,
        stage_failures: list[str],
        log_entries: list[_StageLogEntry],
        fn,
        default,
    ):
        """Execute an async stage function with timing and error isolation."""
        start = time.monotonic()
        try:
            result = await fn()
            elapsed_ms = int((time.monotonic() - start) * 1000)
            log_entries.append(_StageLogEntry(
                stage=stage_name,
                status=StageStatus.SUCCESS,
                duration_ms=elapsed_ms,
                stage_metadata={"event_id": str(event.id)},
            ))
            return result
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            stage_failures.append(stage_name)
            log_entries.append(_StageLogEntry(
                stage=stage_name,
                status=StageStatus.FAILED,
                duration_ms=elapsed_ms,
                error_message=str(exc),
                stage_metadata={"event_id": str(event.id)},
            ))
            logger.warning(
                f"Pipeline stage '{stage_name}' failed",
                extra={"context": {"event_id": str(event.id), "error": str(exc)}},
            )
            return default

    # ── Stage implementations ────────────────────────────────────────────

    def _stage_cleaning(self, event: CollectedEvent) -> tuple[str, str]:
        result = self._cleaner.clean(
            title=event.title,
            summary=event.summary,
            source_url=event.source_url,
        )
        return result.title, result.summary

    def _stage_classification(
        self, title: str, summary: str, event: CollectedEvent
    ) -> AICategory:
        return self._classifier.classify(
            title=title,
            summary=summary,
            organization=event.organization,
            tags=event.tags if isinstance(event.tags, list) else [],
            event_type=event.event_type.value if event.event_type else "",
        )

    def _stage_tagging(
        self, title: str, summary: str, event: CollectedEvent
    ) -> list[str]:
        return self._tagger.extract_tags(
            title=title,
            summary=summary,
            organization=event.organization,
            existing_tags=event.tags if isinstance(event.tags, list) else [],
            extra_metadata=event.extra_metadata if isinstance(event.extra_metadata, dict) else {},
        )

    def _stage_entities(
        self, title: str, summary: str, event: CollectedEvent
    ) -> dict:
        return self._entity_extractor.extract_entities(
            title=title,
            summary=summary,
            organization=event.organization,
            extra_metadata=event.extra_metadata if isinstance(event.extra_metadata, dict) else {},
        )

    def _stage_importance(
        self, title: str, summary: str, event: CollectedEvent, category: AICategory
    ) -> tuple[int, str]:
        return self._scorer.score(
            title=title,
            summary=summary,
            source=event.source,
            source_url=event.source_url,
            organization=event.organization,
            ai_category=category,
            published_at=event.published_at,
            extra_metadata=event.extra_metadata if isinstance(event.extra_metadata, dict) else {},
        )

    async def _stage_summary(
        self, title: str, summary: str, event: CollectedEvent, category: AICategory
    ) -> str:
        return await self._summarizer.summarize(
            title=title,
            content=summary,
            organization=event.organization,
            category=category.value,
        )
