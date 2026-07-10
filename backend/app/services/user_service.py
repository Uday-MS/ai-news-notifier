"""User service — profile, interests, and preferences business logic."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ValidationError
from app.models.user import User
from app.models.user_profile import UserInterest, UserOpportunityPreference
from app.repositories.user_repository import UserRepository
from app.schemas.user import InterestsUpdate, PreferencesUpdate, ProfileUpdate, UserResponse


class UserService:
    """Encapsulates user profile business logic."""

    def __init__(self, user_repo: UserRepository, db: AsyncSession) -> None:
        self._user_repo = user_repo
        self._db = db

    # ── Profile ──────────────────────────────────────────────────────────

    async def get_profile(self, user: User) -> UserResponse:
        """Return full user profile."""
        return UserResponse.from_user(user)

    async def update_profile(self, user: User, data: ProfileUpdate) -> UserResponse:
        """Update user profile fields."""
        update_data: dict[str, Any] = {}

        for field, value in data.model_dump(exclude_unset=True).items():
            if field == "timezone":
                update_data["user_timezone"] = value
            elif field == "username" and value is not None:
                # Check uniqueness
                existing = await self._db.execute(
                    select(User).where(User.username == value, User.id != user.id)
                )
                if existing.scalar_one_or_none():
                    raise ConflictError("Username is already taken.")
                update_data[field] = value
            else:
                update_data[field] = value

        if not update_data:
            return UserResponse.from_user(user)

        updated_user = await self._user_repo.update(user.id, **update_data)
        if not updated_user:
            raise ValidationError("Failed to update profile.")
        return UserResponse.from_user(updated_user)

    # ── Interests ────────────────────────────────────────────────────────

    async def get_interests(self, user_id: uuid.UUID) -> list[str]:
        """Get all interests for a user."""
        result = await self._db.execute(
            select(UserInterest.interest).where(UserInterest.user_id == user_id)
        )
        return list(result.scalars().all())

    async def update_interests(
        self, user_id: uuid.UUID, data: InterestsUpdate
    ) -> list[str]:
        """Replace all interests for a user."""
        # Delete existing
        await self._db.execute(
            delete(UserInterest).where(UserInterest.user_id == user_id)
        )
        # Insert new
        for interest in data.interests:
            self._db.add(UserInterest(user_id=user_id, interest=interest))
        await self._db.flush()
        return data.interests

    # ── Preferences ──────────────────────────────────────────────────────

    async def get_preferences(self, user: User) -> dict:
        """Get opportunity preferences and notification preference."""
        result = await self._db.execute(
            select(UserOpportunityPreference.preference).where(
                UserOpportunityPreference.user_id == user.id
            )
        )
        return {
            "opportunity_preferences": list(result.scalars().all()),
            "notification_preference": user.notification_preference,
        }

    async def update_preferences(
        self, user_id: uuid.UUID, data: PreferencesUpdate
    ) -> list[str]:
        """Replace all opportunity preferences for a user."""
        await self._db.execute(
            delete(UserOpportunityPreference).where(
                UserOpportunityPreference.user_id == user_id
            )
        )
        for pref in data.opportunity_preferences:
            self._db.add(
                UserOpportunityPreference(user_id=user_id, preference=pref)
            )
        await self._db.flush()
        return data.opportunity_preferences
