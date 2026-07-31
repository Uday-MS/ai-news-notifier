"""Delivery API router — notification delivery management endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.database.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.notification import NotificationChannel
from app.models.user import User
from app.services.delivery_service import NotificationDeliveryService

router = APIRouter(prefix="/delivery", tags=["delivery"])


# ── Send Single Notification ─────────────────────────────────────────────


@router.post("/send/{notification_id}", response_model=None)
async def send_notification(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Deliver a single notification through its assigned channel provider."""
    service = NotificationDeliveryService(db)
    result = await service.send(notification_id, user.id)
    return success_response(
        data={
            "notification_id": str(notification_id),
            "channel": result.channel.value,
            "provider": result.provider_name,
            "success": result.success,
            "message": result.message,
            "delivered_at": result.delivered_at.isoformat()
            if result.delivered_at else None,
            "error": result.error,
        },
        message="Notification delivered." if result.success else "Delivery failed.",
    )


# ── Send All Pending ─────────────────────────────────────────────────────


@router.post("/send-pending", response_model=None)
async def send_pending(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Deliver all pending notifications for the current user."""
    service = NotificationDeliveryService(db)
    result = await service.send_pending(user.id, limit=limit)
    return success_response(
        data=result,
        message=f"Delivered {result['delivered']} of {result['total']} notification(s).",
    )


# ── Delivery Status ──────────────────────────────────────────────────────


@router.get("/status/{notification_id}", response_model=None)
async def get_delivery_status(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Check the delivery status of a notification."""
    service = NotificationDeliveryService(db)
    result = await service.get_delivery_status(notification_id, user.id)
    return success_response(data=result)


# ── List Providers ───────────────────────────────────────────────────────


@router.get("/providers", response_model=None)
async def list_providers(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List all available delivery providers and their status."""
    service = NotificationDeliveryService(db)
    providers = service.list_providers()
    return success_response(data={"providers": providers})


# ── Test Channel ─────────────────────────────────────────────────────────


@router.post("/test/{channel}", response_model=None)
async def test_channel(
    channel: NotificationChannel,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Test a delivery channel with a dummy payload (no persistence)."""
    service = NotificationDeliveryService(db)
    result = await service.test_channel(channel)
    return success_response(
        data={
            "channel": result.channel.value,
            "provider": result.provider_name,
            "success": result.success,
            "message": result.message,
        },
        message="Channel test complete.",
    )
