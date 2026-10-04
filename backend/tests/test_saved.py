"""Tests for Saved Articles API."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import CollectedEvent, EventType
from app.models.processed_event import ProcessedEvent, AICategory, ProcessingStatus


# ── Helpers ──────────────────────────────────────────────────────────────


async def _login(client: AsyncClient, db: AsyncSession | None = None) -> dict:
    """Create a verified user + login and return auth headers.

    Phase 4 requires email verification before login, so we create
    the user directly in the DB as verified.
    """
    from app.core.security import hash_password
    from app.models.user import User, UserRole

    if db is not None:
        # Create verified user directly in DB
        user = User(
            email="saved@test.com",
            hashed_password=hash_password("StrongP@ss1"),
            full_name="Saved User",
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        await db.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "saved@test.com", "password": "StrongP@ss1"},
    )
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_article(db: AsyncSession) -> uuid.UUID:
    """Create a collected + processed event, return processed_event id."""
    now = datetime.now(timezone.utc)
    uid = uuid.uuid4().hex[:12]

    event = CollectedEvent(
        id=uuid.uuid4(),
        title=f"Test Article {uid}",
        summary="A test summary.",
        source_url=f"https://example.com/{uid}",
        source="test",
        event_type=EventType.NEWS,
        organization="TestOrg",
        published_at=now,
        collector_id="test-collector",
        content_hash=uuid.uuid4().hex,
    )
    db.add(event)
    await db.flush()

    processed = ProcessedEvent(
        id=uuid.uuid4(),
        collected_event_id=event.id,
        cleaned_title=f"Test Article {uid}",
        cleaned_summary="A test article summary.",
        ai_summary="AI generated summary for saving test.",
        ai_category=AICategory.AI_MODEL,
        ai_tags=["test", "save"],
        importance_score=75,
        importance_reason="test importance",
        entities={},
        processing_status=ProcessingStatus.READY,
        processed_at=now,
    )
    db.add(processed)
    await db.commit()
    return processed.id


# ── Tests ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestSavedArticlesAPI:
    """Test saved articles CRUD endpoints."""

    async def test_save_article(self, client: AsyncClient, db_session: AsyncSession):
        headers = await _login(client, db_session)
        event_id = await _create_article(db_session)

        resp = await client.post(f"/api/v1/saved/{event_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["event_id"] == str(event_id)

    async def test_save_duplicate_is_idempotent(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        headers = await _login(client, db_session)
        event_id = await _create_article(db_session)

        await client.post(f"/api/v1/saved/{event_id}", headers=headers)
        resp = await client.post(f"/api/v1/saved/{event_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_list_saved(self, client: AsyncClient, db_session: AsyncSession):
        headers = await _login(client, db_session)
        e1 = await _create_article(db_session)
        e2 = await _create_article(db_session)

        await client.post(f"/api/v1/saved/{e1}", headers=headers)
        await client.post(f"/api/v1/saved/{e2}", headers=headers)

        resp = await client.get("/api/v1/saved", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]["items"]) == 2
        assert data["data"]["pagination"]["total"] == 2

    async def test_check_saved(self, client: AsyncClient, db_session: AsyncSession):
        headers = await _login(client, db_session)
        event_id = await _create_article(db_session)

        # Not saved yet
        resp = await client.get(f"/api/v1/saved/{event_id}/check", headers=headers)
        assert resp.json()["data"]["is_saved"] is False

        # Save it
        await client.post(f"/api/v1/saved/{event_id}", headers=headers)

        # Now saved
        resp = await client.get(f"/api/v1/saved/{event_id}/check", headers=headers)
        assert resp.json()["data"]["is_saved"] is True

    async def test_unsave_article(self, client: AsyncClient, db_session: AsyncSession):
        headers = await _login(client, db_session)
        event_id = await _create_article(db_session)

        await client.post(f"/api/v1/saved/{event_id}", headers=headers)
        resp = await client.delete(f"/api/v1/saved/{event_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Verify removed
        resp = await client.get(f"/api/v1/saved/{event_id}/check", headers=headers)
        assert resp.json()["data"]["is_saved"] is False

    async def test_unsave_nonexistent(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        headers = await _login(client, db_session)
        fake_id = uuid.uuid4()
        resp = await client.delete(f"/api/v1/saved/{fake_id}", headers=headers)
        assert resp.json()["success"] is False

    async def test_list_empty(self, client: AsyncClient, db_session: AsyncSession):
        headers = await _login(client, db_session)
        resp = await client.get("/api/v1/saved", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["items"] == []
        assert data["data"]["pagination"]["total"] == 0

    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/saved")
        assert resp.status_code == 401
