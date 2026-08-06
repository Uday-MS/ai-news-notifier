"""Saved Article model — tracks user bookmarks."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SavedArticle(Base):
    """A user's saved/bookmarked processed event."""

    __tablename__ = "saved_articles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    processed_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processed_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "processed_event_id", name="uq_saved_user_event"),
    )

    def __repr__(self) -> str:
        return f"<SavedArticle user={self.user_id} event={self.processed_event_id}>"
