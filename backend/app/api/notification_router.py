"""Notification API router — user notification management endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.database.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.notification import NotificationStatus
from app.models.user import User
from app.schemas.notification import NotificationGenerateRequest
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ── List Notifications ───────────────────────────────────────────────────


@router.get("", response_model=None)
async def list_notifications(
    status: str | None = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List the current user's notifications with optional status filter."""
    service = NotificationService(db)
    status_enum = NotificationStatus(status) if status else None
    result = await service.list_notifications(
        user.id, status=status_enum, limit=limit, offset=offset
    )
    return success_response(data=result.model_dump())


# ── Unread Notifications ─────────────────────────────────────────────────


@router.get("/unread", response_model=None)
async def get_unread(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List unread notifications (pending + delivered)."""
    service = NotificationService(db)
    result = await service.get_unread(user.id, limit=limit, offset=offset)
    return success_response(data=result.model_dump())


# ── Generate Notifications ───────────────────────────────────────────────


@router.post("/generate", response_model=None)
async def generate_notifications(
    body: NotificationGenerateRequest | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate notifications from the user's personalized recommendations."""
    params = body or NotificationGenerateRequest()
    service = NotificationService(db)
    result = await service.generate_for_user(
        user,
        min_score=params.min_score,
        max_count=params.max_count,
        cooldown_minutes=params.cooldown_minutes,
        max_per_cooldown=params.max_per_cooldown,
    )
    return success_response(
        data=result.model_dump(),
        message=f"Generated {result.generated} notification(s).",
    )


# ── Single Notification Detail ───────────────────────────────────────────


@router.get("/{notification_id}", response_model=None)
async def get_notification(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get a single notification by ID."""
    service = NotificationService(db)
    result = await service.get_notification(notification_id, user.id)
    return success_response(data=result.model_dump())


# ── Mark Single as Read ──────────────────────────────────────────────────


@router.patch("/{notification_id}/read", response_model=None)
async def mark_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Mark a single notification as read."""
    service = NotificationService(db)
    result = await service.mark_read(notification_id, user.id)
    return success_response(
        data=result.model_dump(),
        message="Notification marked as read.",
    )


# ── Mark All as Read ─────────────────────────────────────────────────────


@router.patch("/read-all", response_model=None)
async def mark_all_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Mark all unread notifications as read."""
    service = NotificationService(db)
    count = await service.mark_all_read(user.id)
    return success_response(
        data={"updated_count": count},
        message=f"Marked {count} notification(s) as read.",
    )


# ── Delete Notification ──────────────────────────────────────────────────


@router.delete("/{notification_id}", response_model=None)
async def delete_notification(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Delete a notification."""
    service = NotificationService(db)
    await service.delete_notification(notification_id, user.id)
    return success_response(message="Notification deleted.")
