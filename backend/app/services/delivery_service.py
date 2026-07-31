"""Notification delivery service — orchestrates delivery through providers.

Consumes NotificationService (Sprint 7) for payload preparation and
NotificationRepository for status updates. Resolves providers by channel
and handles retries for transient failures.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.notification import NotificationChannel, NotificationStatus
from app.repositories.notification_repository import NotificationRepository
from app.services.delivery_providers import (
    ALL_PROVIDERS,
    BaseDeliveryProvider,
    DeliveryConfig,
    DeliveryResult,
)
from app.services.notification_service import NotificationService

logger = get_logger("delivery.service")


class NotificationDeliveryService:
    """Orchestrates notification delivery through channel-specific providers.

    Consumes Sprint 7's NotificationService and NotificationRepository.
    """

    def __init__(
        self,
        db: AsyncSession,
        config: DeliveryConfig | None = None,
    ) -> None:
        self._db = db
        self._config = config or DeliveryConfig()
        self._notification_service = NotificationService(db)
        self._repo = NotificationRepository(db)

        # Build channel → provider registry
        self._providers: dict[NotificationChannel, BaseDeliveryProvider] = {}
        for provider_cls in ALL_PROVIDERS:
            provider = provider_cls()
            if provider.channel in self._config.enabled_channels:
                self._providers[provider.channel] = provider

    # ── Single Delivery ──────────────────────────────────────────────────

    async def send(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> DeliveryResult:
        """Deliver a single notification.

        Fetches the notification, resolves the provider, calls deliver(),
        and updates the notification status on success.
        """
        # Fetch notification (raises NotFoundError if missing)
        notification = await self._repo.get_by_id(notification_id, user_id)
        if notification is None:
            raise NotFoundError("Notification not found.")

        # Check already delivered
        if notification.status == NotificationStatus.DELIVERED:
            raise ConflictError("Notification already delivered.")
        if notification.status == NotificationStatus.READ:
            raise ConflictError("Notification already read.")

        # Resolve provider
        provider = self._providers.get(notification.channel)
        if provider is None:
            raise ValidationError(
                f"Channel '{notification.channel.value}' is not enabled or supported."
            )

        # Prepare payload using Sprint 7 hook
        payload = NotificationService.prepare_delivery_payload(notification)

        # Deliver with retry
        result = await self._deliver_with_retry(provider, payload)

        # Update status on success
        if result.success and result.delivered_at:
            notification.status = NotificationStatus.DELIVERED
            notification.delivered_at = result.delivered_at
            await self._db.flush()
            await self._db.refresh(notification)

        logger.info(
            "Delivery attempt complete",
            extra={"context": {
                "notification_id": str(notification_id),
                "channel": notification.channel.value,
                "success": result.success,
                "provider": result.provider_name,
            }},
        )

        return result

    # ── Batch Delivery ───────────────────────────────────────────────────

    async def send_pending(
        self,
        user_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Deliver all pending notifications for a user.

        Returns a summary with total, delivered, failed counts and results.
        """
        pending = await self._repo.list_for_user(
            user_id, status=NotificationStatus.PENDING, limit=limit
        )

        results: list[dict[str, Any]] = []
        delivered = 0
        failed = 0

        for notification in pending:
            try:
                result = await self.send(notification.id, user_id)
                results.append({
                    "notification_id": str(notification.id),
                    "success": result.success,
                    "channel": result.channel.value,
                    "message": result.message,
                })
                if result.success:
                    delivered += 1
                else:
                    failed += 1
            except (ConflictError, ValidationError) as exc:
                results.append({
                    "notification_id": str(notification.id),
                    "success": False,
                    "channel": notification.channel.value,
                    "message": exc.message,
                })
                failed += 1

        return {
            "total": len(pending),
            "delivered": delivered,
            "failed": failed,
            "results": results,
        }

    # ── Status ───────────────────────────────────────────────────────────

    async def get_delivery_status(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Return the current delivery status of a notification."""
        notification = await self._repo.get_by_id(notification_id, user_id)
        if notification is None:
            raise NotFoundError("Notification not found.")

        return {
            "notification_id": str(notification.id),
            "status": notification.status.value,
            "channel": notification.channel.value,
            "delivered_at": notification.delivered_at.isoformat()
            if notification.delivered_at else None,
        }

    # ── Providers ────────────────────────────────────────────────────────

    def list_providers(self) -> list[dict[str, Any]]:
        """Return info about all registered providers."""
        result = []
        for provider_cls in ALL_PROVIDERS:
            provider = provider_cls()
            info = provider.provider_info()
            info["enabled"] = provider.channel in self._config.enabled_channels
            result.append(info)
        return result

    # ── Test Channel ─────────────────────────────────────────────────────

    async def test_channel(self, channel: NotificationChannel) -> DeliveryResult:
        """Send a test payload through a provider without persisting."""
        provider = self._providers.get(channel)
        if provider is None:
            raise ValidationError(
                f"Channel '{channel.value}' is not enabled or supported."
            )

        test_payload = {
            "notification_id": "test-" + str(uuid.uuid4())[:8],
            "user_id": "test-user",
            "channel": channel.value,
            "title": "Test Notification",
            "message": "This is a test delivery.",
            "notification_type": "recommendation",
            "recommendation_score": 0.0,
            "processed_event_id": "test-event",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        result = await provider.deliver(test_payload)

        logger.info(
            "Channel test complete",
            extra={"context": {
                "channel": channel.value,
                "success": result.success,
            }},
        )

        return result

    # ── Internal ─────────────────────────────────────────────────────────

    async def _deliver_with_retry(
        self,
        provider: BaseDeliveryProvider,
        payload: dict[str, Any],
    ) -> DeliveryResult:
        """Attempt delivery with configurable retries."""
        last_result: DeliveryResult | None = None

        for attempt in range(1, self._config.max_retries + 1):
            result = await provider.deliver(payload)
            if result.success:
                return result

            last_result = result
            logger.warning(
                f"Delivery attempt {attempt}/{self._config.max_retries} failed",
                extra={"context": {
                    "provider": provider.name,
                    "error": result.error,
                    "notification_id": payload.get("notification_id"),
                }},
            )

        # All retries exhausted — return last failure
        return last_result or DeliveryResult(
            success=False,
            channel=provider.channel,
            provider_name=provider.name,
            message="Delivery failed after all retries.",
            error="Max retries exhausted.",
        )
