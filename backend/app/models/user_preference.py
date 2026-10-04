"""UserPreference model — per-user recommendation configuration."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class UserPreference(Base):
    """Stores recommendation preferences for a user.

    One row per user. JSON columns allow flexible preference lists
    without extra join tables.
    """

    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    preferred_categories: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )
    preferred_sources: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )
    muted_categories: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )
    muted_sources: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )
    preferred_technologies: Mapped[list | None] = mapped_column(
        JSON, default=list, nullable=True
    )
    preferred_organizations: Mapped[list | None] = mapped_column(
        JSON, default=list, nullable=True
    )

    __table_args__ = (
        Index("ix_user_preferences_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<UserPreference user_id={self.user_id}>"
