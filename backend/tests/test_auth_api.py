"""Integration tests for auth API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<!doctype html>" in response.text.lower() or "html" in response.text.lower()

    # Verify JSON response when specifically requested via Accept header
    json_resp = await client.get("/", headers={"Accept": "application/json"})
    assert json_resp.status_code == 200
    assert json_resp.json() == {
        "status": "ok",
        "service": "AI News Notifier API",
    }


@pytest.mark.asyncio
async def test_register_endpoint(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "api@test.com", "password": "StrongP@ss1", "full_name": "API User"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "api@test.com"


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "StrongP@ss1", "full_name": "Dup"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@test.com", "password": "weak", "full_name": "Weak"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_endpoint(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "StrongP@ss1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "WrongPass!"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client: AsyncClient, test_user: User):
    # Login first
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "StrongP@ss1"},
    )
    token = login_resp.json()["data"]["access_token"]

    # Get current user
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_me_no_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_refresh_endpoint(client: AsyncClient, test_user: User):
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "StrongP@ss1"},
    )
    refresh_token = login_resp.json()["data"]["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_forgot_password_endpoint(client: AsyncClient, test_user: User):
    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
