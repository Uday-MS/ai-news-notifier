"""Notification repository — data access for notification persistence.

Follows the same convention as FeedRepository: constructor takes
AsyncSession, no base class, composable query methods.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import (
    Notification,
    NotificationStatus,
    NotificationType,
)


class NotificationRepository:
    """Data access layer for Notification persistence."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Create ───────────────────────────────────────────────────────────

    async def create(self, notification: Notification) -> Notification:
        """Persist a new notification and return it refreshed."""
        self._db.add(notification)
        await self._db.flush()
        await self._db.refresh(notification)
        return notification

    # ── Read ─────────────────────────────────────────────────────────────

    async def get_by_id(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Notification | None:
        """Fetch a single notification scoped to a user."""
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        status: NotificationStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        """List notifications for a user, optionally filtered by status."""
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            stmt = stmt.where(Notification.status == status)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def list_unread(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        """List unread (pending or delivered) notifications for a user."""
        stmt = (
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.status.in_([
                    NotificationStatus.PENDING,
                    NotificationStatus.DELIVERED,
                ]),
            )
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def count_for_user(
        self,
        user_id: uuid.UUID,
        *,
        status: NotificationStatus | None = None,
    ) -> int:
        """Count notifications for a user, optionally filtered by status."""
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id)
        )
        if status is not None:
            stmt = stmt.where(Notification.status == status)
        result = await self._db.execute(stmt)
        return result.scalar() or 0

    async def count_unread(self, user_id: uuid.UUID) -> int:
        """Count unread (pending or delivered) notifications."""
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.status.in_([
                    NotificationStatus.PENDING,
                    NotificationStatus.DELIVERED,
                ]),
            )
        )
        result = await self._db.execute(stmt)
        return result.scalar() or 0

    # ── Update ───────────────────────────────────────────────────────────

    async def mark_read(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Notification | None:
        """Mark a single notification as read."""
        notification = await self.get_by_id(notification_id, user_id)
        if notification is None:
            return None
        notification.status = NotificationStatus.READ
        notification.read_at = datetime.now(notification.created_at.tzinfo or None)
        await self._db.flush()
        await self._db.refresh(notification)
        return notification

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        """Mark all unread notifications as read. Returns count updated."""
        now = datetime.now()
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.status.in_([
                    NotificationStatus.PENDING,
                    NotificationStatus.DELIVERED,
                ]),
            )
            .values(status=NotificationStatus.READ, read_at=now)
        )
        result = await self._db.execute(stmt)
        return result.rowcount

    # ── Delete ───────────────────────────────────────────────────────────

    async def delete(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Delete a notification. Returns True if deleted."""
        stmt = (
            delete(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        result = await self._db.execute(stmt)
        return result.rowcount > 0

    async def delete_old(
        self,
        user_id: uuid.UUID,
        before: datetime,
    ) -> int:
        """Delete notifications created before the given datetime."""
        stmt = (
            delete(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.created_at < before,
            )
        )
        result = await self._db.execute(stmt)
        return result.rowcount

    # ── Duplicate & Cooldown Checks ──────────────────────────────────────

    async def exists(
        self,
        user_id: uuid.UUID,
        processed_event_id: uuid.UUID,
        notification_type: NotificationType,
    ) -> bool:
        """Check whether a notification already exists for this combination."""
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.processed_event_id == processed_event_id,
                Notification.notification_type == notification_type,
            )
        )
        result = await self._db.execute(stmt)
        return (result.scalar() or 0) > 0

    async def count_since(
        self,
        user_id: uuid.UUID,
        since: datetime,
    ) -> int:
        """Count notifications created since a given datetime (for cooldown)."""
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.created_at >= since,
            )
        )
        result = await self._db.execute(stmt)
        return result.scalar() or 0
