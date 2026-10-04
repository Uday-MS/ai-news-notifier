"""ProcessedEvent model — AI-enriched event after pipeline processing."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AICategory(str, enum.Enum):
    """Content classification categories for AI events."""

    AI_MODEL = "ai_model"
    AI_RESEARCH = "ai_research"
    PRODUCT_RELEASE = "product_release"
    OPEN_SOURCE = "open_source"
    STARTUP = "startup"
    FUNDING = "funding"
    HACKATHON = "hackathon"
    INTERNSHIP = "internship"
    COMPETITION = "competition"
    STUDENT_PROGRAM = "student_program"
    SECURITY = "security"
    OTHER = "other"


class ProcessingStatus(str, enum.Enum):
    """Outcome of the AI processing pipeline."""

    READY = "ready"
    FAILED = "failed"
    PARTIAL = "partial"


class ProcessedEvent(Base):
    """An AI-enriched event produced by the processing pipeline.

    Each row maps one-to-one to a CollectedEvent and stores the
    results of all processing stages, including optional LLM enrichment.
    """

    __tablename__ = "processed_events"

    # ── Relationship ─────────────────────────────────────────────────────
    collected_event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("collected_events.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    # ── Stage 1: Cleaned Content ─────────────────────────────────────────
    cleaned_title: Mapped[str] = mapped_column(String(500), nullable=False)
    cleaned_summary: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Stage 2: Classification ──────────────────────────────────────────
    ai_category: Mapped[AICategory] = mapped_column(
        Enum(AICategory), nullable=False, default=AICategory.OTHER
    )

    # ── Stage 3: Tags ────────────────────────────────────────────────────
    ai_tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # ── Stage 4: Entities ────────────────────────────────────────────────
    entities: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # ── Stage 5: Importance ──────────────────────────────────────────────
    importance_score: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    importance_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # ── Stage 6: AI Summary ──────────────────────────────────────────────
    ai_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # ── Stage 7: Quality ─────────────────────────────────────────────────
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus), nullable=False, default=ProcessingStatus.PARTIAL
    )

    # ── Timestamp ────────────────────────────────────────────────────────
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Stage 8: LLM Intelligence (Phase 2) ──────────────────────────────
    why_it_matters: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    intelligence_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    llm_importance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    relevance_signals: Mapped[list | None] = mapped_column(JSON, nullable=True)
    llm_entities: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    llm_keywords: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # ── LLM Traceability ─────────────────────────────────────────────────
    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    llm_prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    llm_processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    llm_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default="pending"
    )
    llm_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_attempt_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=0
    )

    # ── Indexes ──────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_processed_events_ai_category", "ai_category"),
        Index("ix_processed_events_processing_status", "processing_status"),
        Index("ix_processed_events_importance_score", "importance_score"),
        Index("ix_processed_events_processed_at", "processed_at"),
        Index("ix_processed_events_llm_status", "llm_status"),
    )

    def __repr__(self) -> str:
        return (
            f"<ProcessedEvent {self.cleaned_title!r} "
            f"status={self.processing_status.value}>"
        )

