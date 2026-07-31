"""Pydantic schemas for the Notification Delivery Layer."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.notification import NotificationChannel, NotificationStatus


# ── Single Delivery ──────────────────────────────────────────────────────


class DeliveryResponse(BaseModel):
    """Result of delivering a single notification."""

    notification_id: str
    channel: NotificationChannel
    provider: str
    success: bool
    message: str
    delivered_at: datetime | None = None
    error: str | None = None


# ── Batch Delivery ───────────────────────────────────────────────────────


class DeliveryBatchResponse(BaseModel):
    """Result of delivering all pending notifications."""

    total: int
    delivered: int
    failed: int
    results: list[dict]


# ── Status ───────────────────────────────────────────────────────────────


class DeliveryStatusResponse(BaseModel):
    """Current delivery status of a notification."""

    notification_id: str
    status: NotificationStatus
    channel: NotificationChannel
    delivered_at: datetime | None = None


# ── Providers ────────────────────────────────────────────────────────────


class ProviderInfo(BaseModel):
    """Metadata about a delivery provider."""

    name: str
    channel: NotificationChannel
    enabled: bool
    description: str


class ProviderListResponse(BaseModel):
    """List of all delivery providers."""

    providers: list[ProviderInfo]


# ── Test ─────────────────────────────────────────────────────────────────


class DeliveryTestResponse(BaseModel):
    """Result of a channel test delivery."""

    channel: NotificationChannel
    provider: str
    success: bool
    message: str
