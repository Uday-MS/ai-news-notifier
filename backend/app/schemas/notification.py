"""Pydantic schemas for the Notification Engine."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import (
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from app.schemas.feed import PaginationMeta


# ── Request Schemas ──────────────────────────────────────────────────────


class NotificationGenerateRequest(BaseModel):
    """Optional parameters for notification generation."""

    min_score: float = Field(
        default=30.0, ge=0.0, le=100.0,
        description="Minimum recommendation score to generate a notification.",
    )
    max_count: int = Field(
        default=10, ge=1, le=50,
        description="Maximum notifications to generate in this batch.",
    )
    cooldown_minutes: int = Field(
        default=60, ge=0, le=1440,
        description="Cooldown window in minutes. Limits notifications per window.",
    )
    max_per_cooldown: int = Field(
        default=10, ge=1, le=100,
        description="Maximum notifications allowed within the cooldown window.",
    )


# ── Response Schemas ─────────────────────────────────────────────────────


class NotificationItem(BaseModel):
    """Lightweight notification for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notification_type: NotificationType
    channel: NotificationChannel
    title: str
    message: str
    status: NotificationStatus
    recommendation_score: float
    created_at: datetime
    read_at: datetime | None


class NotificationDetail(BaseModel):
    """Full notification detail."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    processed_event_id: UUID
    notification_type: NotificationType
    channel: NotificationChannel
    title: str
    message: str
    status: NotificationStatus
    recommendation_score: float
    delivered_at: datetime | None
    read_at: datetime | None
    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated list of notifications."""

    items: list[NotificationItem]
    pagination: PaginationMeta


class NotificationGenerateResponse(BaseModel):
    """Summary of a notification generation run."""

    generated: int
    skipped_duplicate: int
    skipped_cooldown: int
    skipped_low_score: int


class NotificationStatusResponse(BaseModel):
    """Response after a status-change operation."""

    notification_id: UUID | None = None
    status: str
    updated_count: int = 1
