"""CollectorSource model for registered feed/API sources."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CollectorSource(Base):
    """A registered data source (RSS feed, GitHub repo, blog URL, etc.).

    Allows dynamic addition and management of sources without code changes.
    """

    __tablename__ = "collector_sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    collector_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_collected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    collection_interval_minutes: Mapped[int] = mapped_column(
        Integer, default=60, nullable=False
    )

    def __repr__(self) -> str:
        return f"<CollectorSource {self.name!r} ({self.collector_type})>"
