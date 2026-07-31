"""Tests for the Notification Delivery Layer (Sprint 8).

Tests cover:
- DeliveryProviders (unit): all 4 providers, payload validation, provider info
- NotificationDeliveryService (integration): send, send-pending, retry, status
- API endpoints (HTTP): all 5 endpoints
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.event import CollectedEvent, EventType
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from app.models.processed_event import AICategory, ProcessedEvent, ProcessingStatus
from app.models.user import User, UserRole
from app.repositories.notification_repository import NotificationRepository
from app.services.delivery_providers import (
    ALL_PROVIDERS,
    BaseDeliveryProvider,
    DeliveryConfig,
    DeliveryResult,
    EmailProvider,
    InAppProvider,
    PushProvider,
    REQUIRED_PAYLOAD_KEYS,
    SMSProvider,
)
from app.services.delivery_service import NotificationDeliveryService
from app.services.notification_service import NotificationService


# ── Test Data Helpers ────────────────────────────────────────────────────


def _make_payload(**overrides) -> dict[str, Any]:
    """Build a valid delivery payload."""
    defaults = {
        "notification_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "channel": "in_app",
        "title": "Test Notification",
        "message": "Test message body.",
        "notification_type": "recommendation",
        "recommendation_score": 50.0,
        "processed_event_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    defaults.update(overrides)
    return defaults


async def _seed_event(
    db: AsyncSession,
    *,
    title: str = "Delivery Test Event",
    importance_score: int = 80,
) -> tuple[CollectedEvent, ProcessedEvent]:
    """Create a paired CollectedEvent + ProcessedEvent."""
    ce = CollectedEvent(
        title=title, summary="Summary.", source="test-blog",
        source_url=f"https://example.com/{uuid.uuid4()}",
        published_at=datetime.now(timezone.utc),
        event_type=EventType.NEWS, organization="TestOrg",
        tags=[], extra_metadata={}, collector_id="test",
        content_hash=str(uuid.uuid4())[:64],
    )
    db.add(ce)
    await db.flush()
    await db.refresh(ce)

    pe = ProcessedEvent(
        collected_event_id=ce.id, cleaned_title=title,
        cleaned_summary="Summary.", ai_category=AICategory.AI_MODEL,
        ai_tags=["ai"], entities={},
        importance_score=importance_score,
        importance_reason="Test.", ai_summary="AI Summary.",
        processing_status=ProcessingStatus.READY,
        processed_at=datetime.now(timezone.utc),
    )
    db.add(pe)
    await db.flush()
    await db.refresh(pe)
    return ce, pe


async def _create_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    processed_event_id: uuid.UUID,
    *,
    channel: NotificationChannel = NotificationChannel.IN_APP,
    status: NotificationStatus = NotificationStatus.PENDING,
) -> Notification:
    """Create a notification directly via repository."""
    repo = NotificationRepository(db)
    notif = Notification(
        user_id=user_id,
        processed_event_id=processed_event_id,
        notification_type=NotificationType.RECOMMENDATION,
        channel=channel,
        title="Test Delivery Notification",
        message="Test message.",
        status=status,
        recommendation_score=50.0,
    )
    return await repo.create(notif)


# ══════════════════════════════════════════════════════════════════════════
# Provider Unit Tests
# ══════════════════════════════════════════════════════════════════════════


class TestDeliveryProviders:
    """Unit tests for delivery provider adapters."""

    @pytest.mark.asyncio
    async def test_in_app_delivers_successfully(self):
        provider = InAppProvider()
        payload = _make_payload()
        result = await provider.deliver(payload)
        assert result.success is True
        assert result.channel == NotificationChannel.IN_APP
        assert result.provider_name == "in_app"
        assert result.delivered_at is not None
        assert result.error is None

    @pytest.mark.asyncio
    async def test_email_simulates_delivery(self):
        provider = EmailProvider()
        payload = _make_payload(channel="email")
        result = await provider.deliver(payload)
        assert result.success is True
        assert result.channel == NotificationChannel.EMAIL
        assert result.provider_name == "email"
        assert "placeholder" in result.message.lower()

    @pytest.mark.asyncio
    async def test_push_simulates_delivery(self):
        provider = PushProvider()
        payload = _make_payload(channel="push")
        result = await provider.deliver(payload)
        assert result.success is True
        assert result.channel == NotificationChannel.PUSH
        assert result.provider_name == "push"
        assert "placeholder" in result.message.lower()

    @pytest.mark.asyncio
    async def test_sms_simulates_delivery(self):
        provider = SMSProvider()
        payload = _make_payload(channel="sms")
        result = await provider.deliver(payload)
        assert result.success is True
        assert result.channel == NotificationChannel.SMS
        assert result.provider_name == "sms"
        assert "placeholder" in result.message.lower()

    @pytest.mark.asyncio
    async def test_invalid_payload_rejected(self):
        provider = InAppProvider()
        # Missing required keys
        result = await provider.deliver({"title": "Incomplete"})
        assert result.success is False
        assert result.error is not None
        assert "missing" in result.error.lower()

    @pytest.mark.asyncio
    async def test_empty_payload_rejected(self):
        provider = EmailProvider()
        result = await provider.deliver({})
        assert result.success is False

    def test_validate_payload_with_valid_keys(self):
        provider = InAppProvider()
        payload = _make_payload()
        assert provider.validate_payload(payload) is True

    def test_validate_payload_with_missing_keys(self):
        provider = InAppProvider()
        assert provider.validate_payload({"title": "X"}) is False

    def test_provider_info(self):
        provider = InAppProvider()
        info = provider.provider_info()
        assert info["name"] == "in_app"
        assert info["channel"] == "in_app"
        assert "description" in info

    def test_all_providers_registered(self):
        assert len(ALL_PROVIDERS) == 4
        channels = {p.channel for p in (cls() for cls in ALL_PROVIDERS)}
        assert channels == {
            NotificationChannel.IN_APP,
            NotificationChannel.EMAIL,
            NotificationChannel.PUSH,
            NotificationChannel.SMS,
        }

    def test_delivery_config_defaults(self):
        config = DeliveryConfig()
        assert config.max_retries == 2
        assert config.timeout_seconds == 30
        assert config.default_channel == NotificationChannel.IN_APP
        assert len(config.enabled_channels) == 4

    def test_delivery_config_custom(self):
        config = DeliveryConfig(
            max_retries=5,
            enabled_channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
        )
        assert config.max_retries == 5
        assert len(config.enabled_channels) == 2

    def test_delivery_result_fields(self):
        result = DeliveryResult(
            success=True,
            channel=NotificationChannel.IN_APP,
            provider_name="in_app",
            message="OK",
            delivered_at=datetime.now(timezone.utc),
        )
        assert result.success is True
        assert result.error is None


# ══════════════════════════════════════════════════════════════════════════
# DeliveryService Integration Tests
# ══════════════════════════════════════════════════════════════════════════


class TestDeliveryService:
    """Integration tests for the delivery orchestration layer."""

    @pytest.mark.asyncio
    async def test_send_single_success(self, db_session, test_user):
        _, pe = await _seed_event(db_session)
        await db_session.commit()

        notif = await _create_notification(db_session, test_user.id, pe.id)
        await db_session.flush()

        service = NotificationDeliveryService(db_session)
        result = await service.send(notif.id, test_user.id)

        assert result.success is True
        assert result.channel == NotificationChannel.IN_APP
        assert result.delivered_at is not None

    @pytest.mark.asyncio
    async def test_send_updates_status(self, db_session, test_user):
        _, pe = await _seed_event(db_session)
        await db_session.commit()

        notif = await _create_notification(db_session, test_user.id, pe.id)
        await db_session.flush()

        service = NotificationDeliveryService(db_session)
        await service.send(notif.id, test_user.id)

        # Verify status was updated
        repo = NotificationRepository(db_session)
        updated = await repo.get_by_id(notif.id, test_user.id)
        assert updated.status == NotificationStatus.DELIVERED
        assert updated.delivered_at is not None

    @pytest.mark.asyncio
    async def test_send_already_delivered_raises_conflict(self, db_session, test_user):
        _, pe = await _seed_event(db_session)
        await db_session.commit()

        notif = await _create_notification(
            db_session, test_user.id, pe.id,
            status=NotificationStatus.DELIVERED,
        )
        await db_session.flush()

        service = NotificationDeliveryService(db_session)
        with pytest.raises(Exception) as exc_info:
            await service.send(notif.id, test_user.id)
        assert "already" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_send_already_read_raises_conflict(self, db_session, test_user):
        _, pe = await _seed_event(db_session)
        await db_session.commit()

        notif = await _create_notification(
            db_session, test_user.id, pe.id,
            status=NotificationStatus.READ,
        )
        await db_session.flush()

        service = NotificationDeliveryService(db_session)
        with pytest.raises(Exception) as exc_info:
            await service.send(notif.id, test_user.id)
        assert "already" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_send_not_found_raises(self, db_session, test_user):
        service = NotificationDeliveryService(db_session)
        with pytest.raises(Exception) as exc_info:
            await service.send(uuid.uuid4(), test_user.id)
        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_send_pending_batch(self, db_session, test_user):
        # Create multiple pending notifications
        for i in range(3):
            _, pe = await _seed_event(
                db_session, title=f"Batch Event {i}"
            )
            await db_session.flush()
            await _create_notification(db_session, test_user.id, pe.id)
        await db_session.commit()

        service = NotificationDeliveryService(db_session)
        result = await service.send_pending(test_user.id)

        assert result["total"] == 3
        assert result["delivered"] == 3
        assert result["failed"] == 0
        assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_send_pending_no_pending(self, db_session, test_user):
        service = NotificationDeliveryService(db_session)
        result = await service.send_pending(test_user.id)
        assert result["total"] == 0
        assert result["delivered"] == 0

    @pytest.mark.asyncio
    async def test_send_pending_skips_delivered(self, db_session, test_user):
        _, pe1 = await _seed_event(db_session, title="Pending Event")
        _, pe2 = await _seed_event(db_session, title="Delivered Event")
        await db_session.commit()

        await _create_notification(
            db_session, test_user.id, pe1.id,
            status=NotificationStatus.PENDING,
        )
        await _create_notification(
            db_session, test_user.id, pe2.id,
            status=NotificationStatus.DELIVERED,
        )
        await db_session.flush()

        service = NotificationDeliveryService(db_session)
        result = await service.send_pending(test_user.id)

        # Only the pending one should be processed
        assert result["total"] == 1
        assert result["delivered"] == 1

    @pytest.mark.asyncio
    async def test_get_delivery_status(self, db_session, test_user):
        _, pe = await _seed_event(db_session)
        await db_session.commit()

        notif = await _create_notification(db_session, test_user.id, pe.id)
        await db_session.flush()

        service = NotificationDeliveryService(db_session)
        status = await service.get_delivery_status(notif.id, test_user.id)

        assert status["notification_id"] == str(notif.id)
        assert status["status"] == "pending"
        assert status["channel"] == "in_app"

    @pytest.mark.asyncio
    async def test_get_delivery_status_not_found(self, db_session, test_user):
        service = NotificationDeliveryService(db_session)
        with pytest.raises(Exception) as exc_info:
            await service.get_delivery_status(uuid.uuid4(), test_user.id)
        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_delivery_status_after_send(self, db_session, test_user):
        _, pe = await _seed_event(db_session)
        await db_session.commit()

        notif = await _create_notification(db_session, test_user.id, pe.id)
        await db_session.flush()

        service = NotificationDeliveryService(db_session)
        await service.send(notif.id, test_user.id)

        status = await service.get_delivery_status(notif.id, test_user.id)
        assert status["status"] == "delivered"
        assert status["delivered_at"] is not None

    def test_list_providers(self, db_session):
        service = NotificationDeliveryService(db_session)
        providers = service.list_providers()
        assert len(providers) == 4
        names = {p["name"] for p in providers}
        assert names == {"in_app", "email", "push", "sms"}
        for p in providers:
            assert p["enabled"] is True

    def test_list_providers_with_restricted_config(self, db_session):
        config = DeliveryConfig(
            enabled_channels=[NotificationChannel.IN_APP],
        )
        service = NotificationDeliveryService(db_session, config=config)
        providers = service.list_providers()
        enabled = [p for p in providers if p["enabled"]]
        disabled = [p for p in providers if not p["enabled"]]
        assert len(enabled) == 1
        assert len(disabled) == 3

    @pytest.mark.asyncio
    async def test_test_channel_in_app(self, db_session):
        service = NotificationDeliveryService(db_session)
        result = await service.test_channel(NotificationChannel.IN_APP)
        assert result.success is True
        assert result.channel == NotificationChannel.IN_APP

    @pytest.mark.asyncio
    async def test_test_channel_email(self, db_session):
        service = NotificationDeliveryService(db_session)
        result = await service.test_channel(NotificationChannel.EMAIL)
        assert result.success is True
        assert result.channel == NotificationChannel.EMAIL

    @pytest.mark.asyncio
    async def test_test_channel_disabled_raises(self, db_session):
        config = DeliveryConfig(
            enabled_channels=[NotificationChannel.IN_APP],
        )
        service = NotificationDeliveryService(db_session, config=config)
        with pytest.raises(Exception) as exc_info:
            await service.test_channel(NotificationChannel.EMAIL)
        assert "not enabled" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, db_session, test_user):
        """Test that retry logic attempts delivery multiple times."""
        _, pe = await _seed_event(db_session)
        await db_session.commit()

        notif = await _create_notification(db_session, test_user.id, pe.id)
        await db_session.flush()

        # Use default config (max_retries=2) — InApp always succeeds so
        # this just verifies the retry path doesn't break normal flow
        config = DeliveryConfig(max_retries=3)
        service = NotificationDeliveryService(db_session, config=config)
        result = await service.send(notif.id, test_user.id)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_send_with_email_channel(self, db_session, test_user):
        _, pe = await _seed_event(db_session)
        await db_session.commit()

        notif = await _create_notification(
            db_session, test_user.id, pe.id,
            channel=NotificationChannel.EMAIL,
        )
        await db_session.flush()

        service = NotificationDeliveryService(db_session)
        result = await service.send(notif.id, test_user.id)

        assert result.success is True
        assert result.channel == NotificationChannel.EMAIL
        assert "placeholder" in result.message.lower()

    @pytest.mark.asyncio
    async def test_prepare_delivery_payload_integration(self, db_session, test_user):
        """Verify prepare_delivery_payload works with delivery providers."""
        _, pe = await _seed_event(db_session)
        await db_session.commit()

        notif = await _create_notification(db_session, test_user.id, pe.id)
        await db_session.flush()

        payload = NotificationService.prepare_delivery_payload(notif)
        provider = InAppProvider()
        result = await provider.deliver(payload)
        assert result.success is True


# ══════════════════════════════════════════════════════════════════════════
# API Endpoint Tests
# ══════════════════════════════════════════════════════════════════════════


@pytest_asyncio.fixture
async def delivery_auth_user(db_session: AsyncSession) -> tuple[User, str]:
    """Create a user and return (user, access_token)."""
    user = User(
        id=uuid.uuid4(),
        email="delivery_api_test@example.com",
        hashed_password=hash_password("StrongP@ss1"),
        full_name="Delivery Test User",
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(str(user.id), {"role": user.role.value})
    return user, token


@pytest_asyncio.fixture
async def delivery_client(db_session: AsyncSession, delivery_auth_user):
    """Test HTTP client with auth for delivery tests."""
    from app.database.session import get_db
    from app.main import app

    user, token = delivery_auth_user

    async def _override():
        yield db_session

    app.dependency_overrides[get_db] = _override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.headers["Authorization"] = f"Bearer {token}"
        yield ac, user
    app.dependency_overrides.clear()


class TestDeliveryAPI:
    """Tests for all 5 delivery API endpoints."""

    @pytest.mark.asyncio
    async def test_send_notification(self, db_session, delivery_client):
        client, user = delivery_client
        _, pe = await _seed_event(db_session)
        await db_session.commit()

        notif = await _create_notification(db_session, user.id, pe.id)
        await db_session.flush()

        resp = await client.post(f"/api/v1/delivery/send/{notif.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["success"] is True
        assert data["data"]["channel"] == "in_app"
        assert data["data"]["delivered_at"] is not None

    @pytest.mark.asyncio
    async def test_send_not_found(self, delivery_client):
        client, _ = delivery_client
        fake_id = str(uuid.uuid4())
        resp = await client.post(f"/api/v1/delivery/send/{fake_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_send_already_delivered(self, db_session, delivery_client):
        client, user = delivery_client
        _, pe = await _seed_event(db_session)
        await db_session.commit()

        notif = await _create_notification(
            db_session, user.id, pe.id,
            status=NotificationStatus.DELIVERED,
        )
        await db_session.flush()

        resp = await client.post(f"/api/v1/delivery/send/{notif.id}")
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_send_pending_batch(self, db_session, delivery_client):
        client, user = delivery_client

        for i in range(3):
            _, pe = await _seed_event(db_session, title=f"API Batch {i}")
            await db_session.flush()
            await _create_notification(db_session, user.id, pe.id)
        await db_session.commit()

        resp = await client.post("/api/v1/delivery/send-pending")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["total"] == 3
        assert data["data"]["delivered"] == 3

    @pytest.mark.asyncio
    async def test_send_pending_empty(self, delivery_client):
        client, _ = delivery_client
        resp = await client.post("/api/v1/delivery/send-pending")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_get_delivery_status(self, db_session, delivery_client):
        client, user = delivery_client
        _, pe = await _seed_event(db_session)
        await db_session.commit()

        notif = await _create_notification(db_session, user.id, pe.id)
        await db_session.flush()

        resp = await client.get(f"/api/v1/delivery/status/{notif.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_delivery_status_after_send(self, db_session, delivery_client):
        client, user = delivery_client
        _, pe = await _seed_event(db_session)
        await db_session.commit()

        notif = await _create_notification(db_session, user.id, pe.id)
        await db_session.flush()

        # Send first
        await client.post(f"/api/v1/delivery/send/{notif.id}")

        # Check status
        resp = await client.get(f"/api/v1/delivery/status/{notif.id}")
        data = resp.json()
        assert data["data"]["status"] == "delivered"
        assert data["data"]["delivered_at"] is not None

    @pytest.mark.asyncio
    async def test_get_delivery_status_not_found(self, delivery_client):
        client, _ = delivery_client
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/api/v1/delivery/status/{fake_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_providers(self, delivery_client):
        client, _ = delivery_client
        resp = await client.get("/api/v1/delivery/providers")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        providers = data["data"]["providers"]
        assert len(providers) == 4
        names = {p["name"] for p in providers}
        assert names == {"in_app", "email", "push", "sms"}

    @pytest.mark.asyncio
    async def test_test_channel_in_app(self, delivery_client):
        client, _ = delivery_client
        resp = await client.post("/api/v1/delivery/test/in_app")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["success"] is True
        assert data["data"]["channel"] == "in_app"

    @pytest.mark.asyncio
    async def test_test_channel_email(self, delivery_client):
        client, _ = delivery_client
        resp = await client.post("/api/v1/delivery/test/email")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["success"] is True

    @pytest.mark.asyncio
    async def test_test_channel_push(self, delivery_client):
        client, _ = delivery_client
        resp = await client.post("/api/v1/delivery/test/push")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_test_channel_sms(self, delivery_client):
        client, _ = delivery_client
        resp = await client.post("/api/v1/delivery/test/sms")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_no_auth_returns_401_or_403(self, db_session):
        from app.database.session import get_db
        from app.main import app

        async def _override():
            yield db_session

        app.dependency_overrides[get_db] = _override
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/delivery/providers")
            assert resp.status_code in (401, 403)

            resp = await ac.post("/api/v1/delivery/send-pending")
            assert resp.status_code in (401, 403, 422)
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_full_roundtrip(self, db_session, delivery_client):
        """Create notification → Send → Verify status."""
        client, user = delivery_client
        _, pe = await _seed_event(db_session)
        await db_session.commit()

        notif = await _create_notification(db_session, user.id, pe.id)
        await db_session.flush()

        # Status before send
        resp = await client.get(f"/api/v1/delivery/status/{notif.id}")
        assert resp.json()["data"]["status"] == "pending"

        # Send
        resp = await client.post(f"/api/v1/delivery/send/{notif.id}")
        assert resp.json()["data"]["success"] is True

        # Status after send
        resp = await client.get(f"/api/v1/delivery/status/{notif.id}")
        assert resp.json()["data"]["status"] == "delivered"

        # Cannot send again
        resp = await client.post(f"/api/v1/delivery/send/{notif.id}")
        assert resp.status_code == 409
