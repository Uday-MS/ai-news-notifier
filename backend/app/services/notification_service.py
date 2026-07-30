"""Notification service — business logic for notification generation and management.

Consumes RecommendationService (Sprint 6) for personalized feed data.
Applies deterministic notification rules without AI decisions or external APIs.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.feed import PaginationMeta
from app.schemas.notification import (
    NotificationDetail,
    NotificationGenerateResponse,
    NotificationItem,
    NotificationListResponse,
)
from app.services.recommendation_service import RecommendationService

logger = get_logger("notification.service")


class NotificationService:
    """Generates and manages notifications from recommendation results.

    Follows the same constructor pattern as RecommendationService:
    receives AsyncSession and constructs internal dependencies.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = NotificationRepository(db)
        self._recommendation_service = RecommendationService(db)

    # ── Generation ───────────────────────────────────────────────────────

    async def generate_for_user(
        self,
        user: User,
        *,
        min_score: float = 30.0,
        max_count: int = 10,
        cooldown_minutes: int = 60,
        max_per_cooldown: int = 10,
    ) -> NotificationGenerateResponse:
        """Generate notifications from the user's personalized recommendations.

        Deterministic rules applied:
        1. Only recommendations above min_score
        2. Skip duplicates (same user + event + type)
        3. Respect cooldown window (max notifications per window)
        4. Cap at max_count per batch
        """
        generated = 0
        skipped_duplicate = 0
        skipped_cooldown = 0
        skipped_low_score = 0

        # Check cooldown budget
        if cooldown_minutes > 0:
            since = datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)
            recent_count = await self._repo.count_since(user.id, since)
            remaining_budget = max(0, max_per_cooldown - recent_count)
        else:
            remaining_budget = max_count

        if remaining_budget == 0:
            logger.info(
                "Cooldown active, no budget remaining",
                extra={"context": {"user_id": str(user.id)}},
            )
            # Fetch recommendations to count how many would have been skipped
            feed = await self._recommendation_service.get_for_you(
                user, limit=max_count
            )
            for item in feed.items:
                if item.recommendation_score < min_score:
                    skipped_low_score += 1
                else:
                    skipped_cooldown += 1
            return NotificationGenerateResponse(
                generated=0,
                skipped_duplicate=0,
                skipped_cooldown=skipped_cooldown,
                skipped_low_score=skipped_low_score,
            )

        # Fetch personalized recommendations (already sorted by score desc)
        effective_limit = min(max_count, remaining_budget)
        # Fetch a larger pool to account for duplicates/low-score filtering
        pool_size = effective_limit * 3
        feed = await self._recommendation_service.get_for_you(
            user, limit=pool_size
        )

        for item in feed.items:
            if generated >= effective_limit:
                break

            # Rule 1: Minimum score threshold
            if item.recommendation_score < min_score:
                skipped_low_score += 1
                continue

            # Rule 2: Duplicate prevention
            already_exists = await self._repo.exists(
                user.id, item.id, NotificationType.RECOMMENDATION
            )
            if already_exists:
                skipped_duplicate += 1
                continue

            # Rule 3: Cooldown re-check (budget may have decreased)
            if cooldown_minutes > 0 and generated > 0:
                current_total = recent_count + generated
                if current_total >= max_per_cooldown:
                    skipped_cooldown += 1
                    continue

            # Create notification
            notification = Notification(
                user_id=user.id,
                processed_event_id=item.id,
                notification_type=NotificationType.RECOMMENDATION,
                channel=NotificationChannel.IN_APP,
                title=item.cleaned_title,
                message=self._build_message(item),
                status=NotificationStatus.PENDING,
                recommendation_score=item.recommendation_score,
            )
            await self._repo.create(notification)
            generated += 1

        logger.info(
            "Notification generation complete",
            extra={"context": {
                "user_id": str(user.id),
                "generated": generated,
                "skipped_duplicate": skipped_duplicate,
                "skipped_cooldown": skipped_cooldown,
                "skipped_low_score": skipped_low_score,
            }},
        )

        return NotificationGenerateResponse(
            generated=generated,
            skipped_duplicate=skipped_duplicate,
            skipped_cooldown=skipped_cooldown,
            skipped_low_score=skipped_low_score,
        )

    # ── Read Operations ──────────────────────────────────────────────────

    async def list_notifications(
        self,
        user_id: uuid.UUID,
        *,
        status: NotificationStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> NotificationListResponse:
        """List notifications with pagination and optional status filter."""
        notifications = await self._repo.list_for_user(
            user_id, status=status, limit=limit, offset=offset
        )
        total = await self._repo.count_for_user(user_id, status=status)

        items = [NotificationItem.model_validate(n) for n in notifications]

        return NotificationListResponse(
            items=items,
            pagination=PaginationMeta(
                limit=limit,
                offset=offset,
                total=total,
                has_more=(offset + limit) < total,
            ),
        )

    async def get_unread(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> NotificationListResponse:
        """List unread notifications (pending + delivered)."""
        notifications = await self._repo.list_unread(
            user_id, limit=limit, offset=offset
        )
        total = await self._repo.count_unread(user_id)

        items = [NotificationItem.model_validate(n) for n in notifications]

        return NotificationListResponse(
            items=items,
            pagination=PaginationMeta(
                limit=limit,
                offset=offset,
                total=total,
                has_more=(offset + limit) < total,
            ),
        )

    async def get_notification(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> NotificationDetail:
        """Get a single notification detail. Raises NotFoundError."""
        notification = await self._repo.get_by_id(notification_id, user_id)
        if notification is None:
            raise NotFoundError("Notification not found.")
        return NotificationDetail.model_validate(notification)

    # ── Status Changes ───────────────────────────────────────────────────

    async def mark_read(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> NotificationDetail:
        """Mark a single notification as read. Raises NotFoundError."""
        notification = await self._repo.mark_read(notification_id, user_id)
        if notification is None:
            raise NotFoundError("Notification not found.")
        return NotificationDetail.model_validate(notification)

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        """Mark all unread notifications as read. Returns count updated."""
        return await self._repo.mark_all_read(user_id)

    # ── Delete ───────────────────────────────────────────────────────────

    async def delete_notification(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Delete a notification. Raises NotFoundError if not found."""
        deleted = await self._repo.delete(notification_id, user_id)
        if not deleted:
            raise NotFoundError("Notification not found.")

    # ── Delivery Preparation (Sprint 8 hook) ─────────────────────────────

    @staticmethod
    def prepare_delivery_payload(notification: Notification) -> dict[str, Any]:
        """Build a structured payload for future email/push/SMS providers.

        Returns a dict that Sprint 8 delivery adapters can consume
        without needing access to the ORM model.
        """
        return {
            "notification_id": str(notification.id),
            "user_id": str(notification.user_id),
            "channel": notification.channel.value,
            "title": notification.title,
            "message": notification.message,
            "notification_type": notification.notification_type.value,
            "recommendation_score": notification.recommendation_score,
            "processed_event_id": str(notification.processed_event_id),
            "created_at": notification.created_at.isoformat()
            if notification.created_at else None,
        }

    # ── Internal Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _build_message(item: Any) -> str:
        """Build a notification message from a recommendation item."""
        parts = []
        if hasattr(item, "ai_summary") and item.ai_summary:
            parts.append(item.ai_summary)
        if hasattr(item, "recommendation_reasons") and item.recommendation_reasons:
            reasons = "; ".join(item.recommendation_reasons[:3])
            parts.append(f"Why: {reasons}")
        return " | ".join(parts) if parts else item.cleaned_title
