"""Notification delivery providers — provider abstraction and adapters.

Contains:
- DeliveryConfig: configurable delivery parameters
- DeliveryResult: provider return value
- BaseDeliveryProvider: abstract base for all channel providers
- InAppProvider: fully functional in-app delivery
- EmailProvider: placeholder for future SMTP/SendGrid integration
- PushProvider: placeholder for future Firebase/OneSignal integration
- SMSProvider: placeholder for future Twilio/AWS SNS integration
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.models.notification import NotificationChannel

logger = get_logger("delivery.providers")

# Required keys in every delivery payload (from NotificationService.prepare_delivery_payload)
REQUIRED_PAYLOAD_KEYS = frozenset({
    "notification_id",
    "user_id",
    "channel",
    "title",
    "message",
})


# ── Configuration ────────────────────────────────────────────────────────


@dataclass
class DeliveryConfig:
    """Configurable delivery parameters."""

    max_retries: int = 2
    timeout_seconds: int = 30
    enabled_channels: list[NotificationChannel] = field(
        default_factory=lambda: list(NotificationChannel)
    )
    default_channel: NotificationChannel = NotificationChannel.IN_APP


# ── Result ───────────────────────────────────────────────────────────────


@dataclass
class DeliveryResult:
    """Return value from a provider delivery attempt."""

    success: bool
    channel: NotificationChannel
    provider_name: str
    message: str
    delivered_at: datetime | None = None
    error: str | None = None


# ── Base Provider ────────────────────────────────────────────────────────


class BaseDeliveryProvider(abc.ABC):
    """Abstract base class for notification delivery providers.

    Subclasses must set `channel` and `name` class attributes and
    implement the `deliver()` method.
    """

    channel: NotificationChannel
    name: str
    description: str = ""

    def validate_payload(self, payload: dict[str, Any]) -> bool:
        """Validate that the payload contains all required keys."""
        return REQUIRED_PAYLOAD_KEYS.issubset(payload.keys())

    @abc.abstractmethod
    async def deliver(self, payload: dict[str, Any]) -> DeliveryResult:
        """Deliver a notification. Must be implemented by subclasses."""
        ...

    def provider_info(self) -> dict[str, Any]:
        """Return metadata about this provider."""
        return {
            "name": self.name,
            "channel": self.channel.value,
            "description": self.description,
        }


# ── In-App Provider (fully functional) ───────────────────────────────────


class InAppProvider(BaseDeliveryProvider):
    """In-app notification delivery.

    Fully functional — marks the notification as delivered. The actual
    display is handled by the frontend reading the notification status.
    """

    channel = NotificationChannel.IN_APP
    name = "in_app"
    description = "In-application notification delivery."

    async def deliver(self, payload: dict[str, Any]) -> DeliveryResult:
        if not self.validate_payload(payload):
            return DeliveryResult(
                success=False,
                channel=self.channel,
                provider_name=self.name,
                message="Delivery failed.",
                error="Invalid payload: missing required fields.",
            )

        now = datetime.now(timezone.utc)
        logger.info(
            "In-app notification delivered",
            extra={"context": {
                "notification_id": payload["notification_id"],
                "user_id": payload["user_id"],
            }},
        )

        return DeliveryResult(
            success=True,
            channel=self.channel,
            provider_name=self.name,
            message="Notification delivered in-app.",
            delivered_at=now,
        )


# ── Email Provider (placeholder) ────────────────────────────────────────


class EmailProvider(BaseDeliveryProvider):
    """Email notification delivery placeholder.

    Validates payloads and simulates successful delivery.
    Replace deliver() with real SMTP/SendGrid integration in a future sprint.
    """

    channel = NotificationChannel.EMAIL
    name = "email"
    description = "Email notification delivery (placeholder)."

    async def deliver(self, payload: dict[str, Any]) -> DeliveryResult:
        if not self.validate_payload(payload):
            return DeliveryResult(
                success=False,
                channel=self.channel,
                provider_name=self.name,
                message="Delivery failed.",
                error="Invalid payload: missing required fields.",
            )

        now = datetime.now(timezone.utc)
        logger.info(
            "Email delivery simulated",
            extra={"context": {
                "notification_id": payload["notification_id"],
                "user_id": payload["user_id"],
                "note": "Placeholder — no real email sent.",
            }},
        )

        return DeliveryResult(
            success=True,
            channel=self.channel,
            provider_name=self.name,
            message="Email delivery simulated (placeholder).",
            delivered_at=now,
        )


# ── Push Provider (placeholder) ──────────────────────────────────────────


class PushProvider(BaseDeliveryProvider):
    """Push notification delivery placeholder.

    Validates payloads and simulates successful delivery.
    Replace deliver() with real Firebase/OneSignal integration in a future sprint.
    """

    channel = NotificationChannel.PUSH
    name = "push"
    description = "Push notification delivery (placeholder)."

    async def deliver(self, payload: dict[str, Any]) -> DeliveryResult:
        if not self.validate_payload(payload):
            return DeliveryResult(
                success=False,
                channel=self.channel,
                provider_name=self.name,
                message="Delivery failed.",
                error="Invalid payload: missing required fields.",
            )

        now = datetime.now(timezone.utc)
        logger.info(
            "Push delivery simulated",
            extra={"context": {
                "notification_id": payload["notification_id"],
                "user_id": payload["user_id"],
                "note": "Placeholder — no real push sent.",
            }},
        )

        return DeliveryResult(
            success=True,
            channel=self.channel,
            provider_name=self.name,
            message="Push delivery simulated (placeholder).",
            delivered_at=now,
        )


# ── SMS Provider (placeholder) ───────────────────────────────────────────


class SMSProvider(BaseDeliveryProvider):
    """SMS notification delivery placeholder.

    Validates payloads and simulates successful delivery.
    Replace deliver() with real Twilio/AWS SNS integration in a future sprint.
    """

    channel = NotificationChannel.SMS
    name = "sms"
    description = "SMS notification delivery (placeholder)."

    async def deliver(self, payload: dict[str, Any]) -> DeliveryResult:
        if not self.validate_payload(payload):
            return DeliveryResult(
                success=False,
                channel=self.channel,
                provider_name=self.name,
                message="Delivery failed.",
                error="Invalid payload: missing required fields.",
            )

        now = datetime.now(timezone.utc)
        logger.info(
            "SMS delivery simulated",
            extra={"context": {
                "notification_id": payload["notification_id"],
                "user_id": payload["user_id"],
                "note": "Placeholder — no real SMS sent.",
            }},
        )

        return DeliveryResult(
            success=True,
            channel=self.channel,
            provider_name=self.name,
            message="SMS delivery simulated (placeholder).",
            delivered_at=now,
        )


# ── Provider Registry Helper ────────────────────────────────────────────

# All available provider classes
ALL_PROVIDERS: list[type[BaseDeliveryProvider]] = [
    InAppProvider,
    EmailProvider,
    PushProvider,
    SMSProvider,
]
