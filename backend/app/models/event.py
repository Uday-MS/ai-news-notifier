"""CollectedEvent model for normalized news/release events."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EventType(str, enum.Enum):
    """Categorisation of collected events."""

    BLOG_POST = "blog_post"
    RELEASE = "release"
    RESEARCH_PAPER = "research_paper"
    ANNOUNCEMENT = "announcement"
    NEWS = "news"


class CollectedEvent(Base):
    """A normalised event ingested by a collector.

    Every collector produces instances of this model through the
    fetch → normalise → validate → emit pipeline.
    """

    __tablename__ = "collected_events"

    # ── Content ──────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2048), unique=True, nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType), nullable=False
    )
    organization: Mapped[str] = mapped_column(String(255), nullable=False)
    tags: Mapped[dict | list] = mapped_column(JSON, default=list, nullable=False)
    extra_metadata: Mapped[dict] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )

    # ── Collector Tracking ───────────────────────────────────────────────
    collector_id: Mapped[str] = mapped_column(String(100), nullable=False)
    content_hash: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    # ── Indexes ──────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_collected_events_published_at", "published_at"),
        Index("ix_collected_events_source", "source"),
        Index("ix_collected_events_event_type", "event_type"),
        Index("ix_collected_events_organization", "organization"),
    )

    def __repr__(self) -> str:
        return f"<CollectedEvent {self.title!r} ({self.source})>"
