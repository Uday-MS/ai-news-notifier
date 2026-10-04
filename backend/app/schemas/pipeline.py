"""Pydantic schemas for the AI Processing Pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.processed_event import AICategory, ProcessingStatus
from app.models.processing_log import StageStatus


# ── ProcessedEvent Schemas ───────────────────────────────────────────────


class ProcessedEventRead(BaseModel):
    """Full API representation of a processed event."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    collected_event_id: UUID
    cleaned_title: str
    cleaned_summary: str
    ai_category: AICategory
    ai_tags: list[str]
    entities: dict[str, Any]
    importance_score: int
    importance_reason: str
    ai_summary: str
    processing_status: ProcessingStatus
    processed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # ── LLM Intelligence (Phase 2) ───────────────────────────────────────
    why_it_matters: str | None = None
    llm_summary: str | None = None
    intelligence_type: str | None = None
    llm_category: str | None = None
    llm_subcategory: str | None = None
    llm_importance_score: int | None = None
    confidence_score: float | None = None
    relevance_signals: list[str] | None = None
    llm_entities: dict[str, Any] | None = None
    llm_keywords: list[str] | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_prompt_version: str | None = None
    llm_processed_at: datetime | None = None
    llm_status: str | None = None
    llm_error: str | None = None
    llm_attempt_count: int | None = None


class ProcessedEventSummary(BaseModel):
    """Lightweight processed event for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    collected_event_id: UUID
    cleaned_title: str
    ai_category: AICategory
    importance_score: int
    processing_status: ProcessingStatus
    ai_tags: list[str]
    processed_at: datetime | None


# ── ProcessingLog Schema ────────────────────────────────────────────────


class ProcessingLogRead(BaseModel):
    """Single processing stage log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    processed_event_id: UUID
    stage: str
    status: StageStatus
    duration_ms: int
    error_message: str | None
    stage_metadata: dict[str, Any]
    created_at: datetime


# ── Pipeline Status ─────────────────────────────────────────────────────


class PipelineStatusResponse(BaseModel):
    """Aggregated processing statistics."""

    total_collected: int
    total_processed: int
    ready: int
    partial: int
    failed: int
    unprocessed: int
