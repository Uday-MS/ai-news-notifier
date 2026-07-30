"""Notification model and supporting enums."""

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
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class NotificationType(str, enum.Enum):
    """Type of notification trigger."""

    RECOMMENDATION = "recommendation"
    TRENDING = "trending"
    BREAKING = "breaking"


class NotificationChannel(str, enum.Enum):
    """Delivery channel for the notification."""

    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"


class NotificationStatus(str, enum.Enum):
    """Lifecycle status of a notification."""

    PENDING = "pending"
    DELIVERED = "delivered"
    READ = "read"
    DISMISSED = "dismissed"


class Notification(Base):
    """User-facing notification generated from recommendation results.

    Each row links a user to a processed event and carries the
    presentation payload (title + message) plus lifecycle metadata.
    """

    __tablename__ = "notifications"

    # ── Relationships ────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    processed_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("processed_events.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Classification ───────────────────────────────────────────────────
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType), nullable=False, default=NotificationType.RECOMMENDATION
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel), nullable=False, default=NotificationChannel.IN_APP
    )

    # ── Content ──────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Status ───────────────────────────────────────────────────────────
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING
    )
    recommendation_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )

    # ── Timestamps ───────────────────────────────────────────────────────
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Constraints & Indexes ────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint(
            "user_id", "processed_event_id", "notification_type",
            name="uq_notification_user_event_type",
        ),
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_status", "status"),
        Index("ix_notifications_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Notification {self.title!r} "
            f"user={self.user_id} status={self.status.value}>"
        )
