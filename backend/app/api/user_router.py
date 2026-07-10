"""User API routes — profile, interests, and preferences."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.database.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import InterestsUpdate, PreferencesUpdate, ProfileUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def _get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Wire up the user service with its repository."""
    return UserService(UserRepository(db), db)


# ── Profile ──────────────────────────────────────────────────────────────


@router.get("/me")
async def get_profile(
    user: User = Depends(get_current_user),
    service: UserService = Depends(_get_user_service),
):
    """Get the full profile of the authenticated user."""
    profile = await service.get_profile(user)
    return success_response(data=profile.model_dump(mode="json"))


@router.put("/me")
async def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    service: UserService = Depends(_get_user_service),
):
    """Update the profile of the authenticated user."""
    profile = await service.update_profile(user, data)
    return success_response(data=profile.model_dump(mode="json"))


# ── Interests ────────────────────────────────────────────────────────────


@router.get("/interests")
async def get_interests(
    user: User = Depends(get_current_user),
    service: UserService = Depends(_get_user_service),
):
    """Get the interests of the authenticated user."""
    interests = await service.get_interests(user.id)
    return success_response(data={"interests": interests})


@router.put("/interests")
async def update_interests(
    data: InterestsUpdate,
    user: User = Depends(get_current_user),
    service: UserService = Depends(_get_user_service),
):
    """Set the interests of the authenticated user."""
    interests = await service.update_interests(user.id, data)
    return success_response(data={"interests": interests})


# ── Preferences ──────────────────────────────────────────────────────────


@router.get("/preferences")
async def get_preferences(
    user: User = Depends(get_current_user),
    service: UserService = Depends(_get_user_service),
):
    """Get the preferences of the authenticated user."""
    prefs = await service.get_preferences(user)
    return success_response(data=prefs)


@router.put("/preferences")
async def update_preferences(
    data: PreferencesUpdate,
    user: User = Depends(get_current_user),
    service: UserService = Depends(_get_user_service),
):
    """Set the opportunity preferences of the authenticated user."""
    prefs = await service.update_preferences(user.id, data)
    return success_response(data={"opportunity_preferences": prefs})
