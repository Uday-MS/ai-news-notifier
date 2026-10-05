"""Intelligence enrichment service — orchestrates LLM enrichment of events.

This service takes processed events and enriches them with structured
intelligence from an external LLM.  It handles idempotency, failure
isolation, and traceability.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, case, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.intelligence_prompt import (
    INTELLIGENCE_PROMPT_VERSION,
    SYSTEM_INSTRUCTION,
    build_extraction_prompt,
)
from app.ai.intelligence_schema import (
    LLMIntelligenceOutput,
    validate_intelligence_output,
)
from app.ai.llm_provider import (
    LLMAuthenticationError,
    LLMProvider,
    LLMProviderError,
    LLMQuotaExhaustedError,
)
from app.core.logging import get_logger
from app.models.event import CollectedEvent
from app.models.processed_event import ProcessedEvent

logger = get_logger("intelligence.service")


class IntelligenceService:
    """Orchestrates LLM intelligence enrichment for processed events."""

    def __init__(self, db: AsyncSession, provider: LLMProvider) -> None:
        self._db = db
        self._provider = provider

    # ── Public API ───────────────────────────────────────────────────────

    async def enrich_single(
        self,
        processed_event_id: uuid.UUID,
        *,
        force: bool = False,
    ) -> ProcessedEvent | None:
        """Enrich a single processed event with LLM intelligence.

        Args:
            processed_event_id: ID of the ProcessedEvent to enrich.
            force: If True, re-enrich even if already completed.

        Returns:
            The updated ProcessedEvent, or None if not found.
        """
        processed = await self._get_processed_event(processed_event_id)
        if processed is None:
            return None

        # Idempotency check
        if not force and processed.llm_status == "completed":
            logger.info(
                "Event already enriched, skipping",
                extra={"context": {"processed_id": str(processed_event_id)}},
            )
            return processed

        # Get the source collected event for grounding
        collected = await self._get_collected_event(processed.collected_event_id)
        if collected is None:
            logger.warning(
                "Collected event not found for processed event",
                extra={"context": {"processed_id": str(processed_event_id)}},
            )
            return processed

        return await self._run_enrichment(processed, collected)

    async def enrich_pending(
        self,
        *,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Enrich all pending processed events.

        Returns:
            Summary dict with counts.
        """
        # Find events that need LLM enrichment, prioritizing pending over failed retries
        stmt = (
            select(ProcessedEvent)
            .where(
                or_(
                    ProcessedEvent.llm_status.in_(["pending", None]),
                    and_(
                        ProcessedEvent.llm_status == "failed",
                        or_(
                            ProcessedEvent.llm_attempt_count == None,  # noqa: E711
                            ProcessedEvent.llm_attempt_count < 3,
                        ),
                    ),
                )
            )
            .order_by(
                case(
                    (ProcessedEvent.llm_status.in_(["pending", None]), 0),
                    else_=1,
                ),
                ProcessedEvent.created_at.asc(),
            )
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        pending = list(result.scalars().all())

        summary: dict[str, Any] = {
            "total": len(pending),
            "enriched": 0,
            "failed": 0,
            "skipped": 0,
        }

        for processed in pending:
            collected = await self._get_collected_event(
                processed.collected_event_id
            )
            if collected is None:
                summary["skipped"] += 1
                continue

            try:
                await self._run_enrichment(processed, collected)
                summary["enriched"] += 1
            except LLMAuthenticationError:
                # Don't continue if auth is broken
                summary["failed"] += 1
                logger.error("LLM authentication failed — stopping batch")
                break
            except LLMQuotaExhaustedError as exc:
                # Daily quota exhausted — stop batch immediately without hammering
                summary["failed"] += 1
                logger.warning(
                    f"LLM quota exhausted — stopping batch: {exc}",
                    extra={"context": {"processed_id": str(processed.id)}},
                )
                break
            except Exception as exc:
                summary["failed"] += 1
                logger.warning(
                    "Enrichment failed for event",
                    extra={
                        "context": {
                            "processed_id": str(processed.id),
                            "error": str(exc),
                        }
                    },
                )

        return summary

    # ── Internal ─────────────────────────────────────────────────────────

    async def _run_enrichment(
        self,
        processed: ProcessedEvent,
        collected: CollectedEvent,
    ) -> ProcessedEvent:
        """Execute LLM enrichment for a single event."""
        # Mark as processing
        processed.llm_status = "processing"
        processed.llm_attempt_count = (processed.llm_attempt_count or 0) + 1
        await self._db.flush()

        try:
            # Build prompt
            published_str = ""
            if collected.published_at:
                published_str = collected.published_at.isoformat()

            prompt = build_extraction_prompt(
                title=collected.title,
                source=collected.source,
                source_url=collected.source_url,
                published_at=published_str,
                content=collected.summary,
            )

            # Call LLM
            raw_output = await self._provider.generate(
                SYSTEM_INSTRUCTION, prompt
            )

            # Validate and sanitise
            intelligence = validate_intelligence_output(raw_output)

            # Quality guard: reject empty/obviously bad output
            if not intelligence.concise_summary or len(intelligence.concise_summary) < 10:
                raise LLMProviderError("LLM returned empty or too-short summary")

            if not intelligence.why_it_matters or len(intelligence.why_it_matters) < 10:
                raise LLMProviderError("LLM returned empty or too-short why_it_matters")

            # Apply to processed event
            self._apply_intelligence(processed, intelligence)

            processed.llm_status = "completed"
            processed.llm_error = None
            processed.llm_processed_at = datetime.now(timezone.utc)
            processed.llm_provider = self._provider.provider_name
            processed.llm_model = self._provider.model_name
            processed.llm_prompt_version = INTELLIGENCE_PROMPT_VERSION

            await self._db.flush()

            logger.info(
                "Event enriched successfully",
                extra={
                    "context": {
                        "processed_id": str(processed.id),
                        "category": intelligence.category,
                        "importance": intelligence.importance_score,
                        "confidence": intelligence.confidence_score,
                    }
                },
            )

            return processed

        except LLMAuthenticationError:
            processed.llm_status = "failed"
            processed.llm_error = "Authentication failed — API key missing or invalid"
            await self._db.flush()
            raise

        except LLMQuotaExhaustedError as exc:
            processed.llm_status = "failed"
            processed.llm_error = f"Quota exhausted: {exc}"[:500]
            await self._db.flush()
            raise

        except Exception as exc:
            processed.llm_status = "failed"
            processed.llm_error = str(exc)[:500]
            await self._db.flush()

            logger.warning(
                "LLM enrichment failed",
                extra={
                    "context": {
                        "processed_id": str(processed.id),
                        "error": str(exc),
                    }
                },
            )
            return processed

    def _apply_intelligence(
        self,
        processed: ProcessedEvent,
        intel: LLMIntelligenceOutput,
    ) -> None:
        """Write validated intelligence fields onto the ProcessedEvent."""
        processed.llm_summary = intel.concise_summary
        processed.why_it_matters = intel.why_it_matters
        processed.llm_category = intel.category
        processed.llm_subcategory = intel.subcategory
        processed.intelligence_type = intel.intelligence_type
        processed.llm_importance_score = intel.importance_score
        processed.confidence_score = intel.confidence_score
        processed.relevance_signals = intel.relevance_signals
        processed.llm_keywords = intel.keywords

        # Build structured entities dict
        processed.llm_entities = {
            "people": intel.entities,
            "technologies": intel.technologies,
            "organizations": intel.organizations,
            "models": intel.models,
        }

    async def _get_processed_event(
        self, event_id: uuid.UUID
    ) -> ProcessedEvent | None:
        result = await self._db.execute(
            select(ProcessedEvent).where(ProcessedEvent.id == event_id)
        )
        return result.scalar_one_or_none()

    async def _get_collected_event(
        self, event_id: uuid.UUID
    ) -> CollectedEvent | None:
        result = await self._db.execute(
            select(CollectedEvent).where(CollectedEvent.id == event_id)
        )
        return result.scalar_one_or_none()
