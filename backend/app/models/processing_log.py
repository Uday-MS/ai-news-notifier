"""ProcessingLog model — per-stage audit trail for pipeline runs."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class StageStatus(str, enum.Enum):
    """Outcome of a single pipeline stage."""

    SUCCESS = "success"
    FAILED = "failed"


class ProcessingLog(Base):
    """Records the result of each processing stage for audit and debugging."""

    __tablename__ = "processing_logs"

    # ── Relationship ─────────────────────────────────────────────────────
    processed_event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("processed_events.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Stage details ────────────────────────────────────────────────────
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[StageStatus] = mapped_column(
        Enum(StageStatus), nullable=False
    )
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    stage_metadata: Mapped[dict] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )

    # ── Indexes ──────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_processing_logs_processed_event_id", "processed_event_id"),
        Index("ix_processing_logs_stage", "stage"),
        Index("ix_processing_logs_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<ProcessingLog stage={self.stage!r} "
            f"status={self.status.value}>"
        )
