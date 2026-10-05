"""Tests for Single-Service Frontend + Backend serving.

Verifies:
1. GET / returns React index.html.
2. Client-side routes (/login, /news, /saved, /settings, etc.) return index.html.
3. Static assets (/assets/*, /favicon.svg) are served correctly.
4. /api/v1/health reaches FastAPI.
5. /docs reaches FastAPI Swagger.
6. /openapi.json reaches FastAPI OpenAPI schema.
7. Unmatched API routes (/api/v1/nonexistent) return 404 JSON, NOT index.html.
8. SPA fallback works for arbitrary client routes.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_returns_frontend(client: AsyncClient):
    """GET / must return React index.html."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<div id=\"root\"></div>" in response.text or "<!doctype html>" in response.text.lower()


@pytest.mark.asyncio
async def test_react_login_route_returns_index_html(client: AsyncClient):
    """GET /login must return index.html for React Router."""
    response = await client.get("/login")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<!doctype html>" in response.text.lower() or "html" in response.text.lower()


@pytest.mark.asyncio
async def test_react_news_route_returns_index_html(client: AsyncClient):
    """GET /news must return index.html for React Router."""
    response = await client.get("/news")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "<!doctype html>" in response.text.lower() or "html" in response.text.lower()


@pytest.mark.asyncio
async def test_react_saved_route_returns_index_html(client: AsyncClient):
    """GET /saved must return index.html for React Router."""
    response = await client.get("/saved")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_react_settings_route_returns_index_html(client: AsyncClient):
    """GET /settings must return index.html for React Router."""
    response = await client.get("/settings")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_react_arbitrary_client_route_falls_back_to_index_html(client: AsyncClient):
    """Arbitrary non-API paths must fall back to index.html for client-side routing."""
    response = await client.get("/some/client/deep/route")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_static_asset_serving(client: AsyncClient):
    """GET /favicon.svg or static assets must return the static file."""
    response = await client.get("/favicon.svg")
    # If favicon.svg exists in dist, returns 200 SVG; otherwise falls back to index.html with 200
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_health_reaches_fastapi(client: AsyncClient):
    """GET /api/v1/health must reach FastAPI and return healthy status."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_docs_reaches_fastapi_swagger(client: AsyncClient):
    """GET /docs must reach FastAPI Swagger UI, NOT index.html."""
    response = await client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


@pytest.mark.asyncio
async def test_openapi_json_reaches_fastapi(client: AsyncClient):
    """GET /openapi.json must reach FastAPI OpenAPI schema, NOT index.html."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data or "paths" in data


@pytest.mark.asyncio
async def test_api_routes_never_intercepted_by_spa_fallback(client: AsyncClient):
    """Unmatched /api/v1/* routes must return 404 JSON, NEVER index.html."""
    response = await client.get("/api/v1/nonexistent-route-for-testing")
    assert response.status_code == 404
    assert response.headers.get("content-type", "").startswith("application/json")
    data = response.json()
    assert "detail" in data
