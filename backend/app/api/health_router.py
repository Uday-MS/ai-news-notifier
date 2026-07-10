"""Health check endpoint for Docker and monitoring."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Simple health check for container orchestration."""
    return {"status": "healthy"}
