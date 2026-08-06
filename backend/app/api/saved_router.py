"""Saved Articles API router — bookmark management endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.database.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.repositories.saved_article_repository import SavedArticleRepository
from app.schemas.feed import PaginationMeta

router = APIRouter(prefix="/saved", tags=["saved"])


# ── Save Article ─────────────────────────────────────────────────────────


@router.post("/{event_id}", response_model=None)
async def save_article(
    event_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Save/bookmark a processed event."""
    repo = SavedArticleRepository(db)
    saved = await repo.save(user.id, event_id)
    await db.commit()
    return success_response(
        data={"saved_article_id": str(saved.id), "event_id": str(event_id)},
        message="Article saved.",
    )


# ── Unsave Article ───────────────────────────────────────────────────────


@router.delete("/{event_id}", response_model=None)
async def unsave_article(
    event_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Remove a saved article."""
    repo = SavedArticleRepository(db)
    deleted = await repo.unsave(user.id, event_id)
    await db.commit()
    if not deleted:
        return {
            "success": False,
            "error": {"code": "NOT_FOUND", "message": "Saved article not found."},
        }
    return success_response(message="Article unsaved.")


# ── List Saved ───────────────────────────────────────────────────────────


@router.get("", response_model=None)
async def list_saved(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """List the current user's saved articles."""
    repo = SavedArticleRepository(db)
    items, total = await repo.get_saved(user.id, limit=limit, offset=offset)

    pagination = PaginationMeta(
        limit=limit, offset=offset, total=total, has_more=(offset + limit < total)
    ).model_dump()

    return success_response(data={"items": items, "pagination": pagination})


# ── Check Saved ──────────────────────────────────────────────────────────


@router.get("/{event_id}/check", response_model=None)
async def check_saved(
    event_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Check if a specific article is saved."""
    repo = SavedArticleRepository(db)
    is_saved = await repo.is_saved(user.id, event_id)
    return success_response(data={"is_saved": is_saved})
