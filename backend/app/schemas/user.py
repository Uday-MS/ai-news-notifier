"""User response and update schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserResponse(BaseModel):
    """Public user representation — includes all profile fields."""

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_verified: bool
    created_at: datetime

    # Profile fields (Sprint 2)
    username: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    college: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Optional[int] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    notification_preference: str = "instant"
    onboarding_completed: bool = False

    model_config = {"from_attributes": True}

    @classmethod
    def from_user(cls, user) -> "UserResponse":
        """Build response handling the user_timezone → timezone mapping."""
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_verified=user.is_verified,
            created_at=user.created_at,
            username=user.username,
            bio=user.bio,
            profile_image=user.profile_image,
            college=user.college,
            degree=user.degree,
            graduation_year=user.graduation_year,
            country=user.country,
            timezone=user.user_timezone,
            notification_preference=user.notification_preference,
            onboarding_completed=user.onboarding_completed,
        )


class ProfileUpdate(BaseModel):
    """Fields that can be updated on the user profile."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    username: Optional[str] = Field(None, min_length=2, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    profile_image: Optional[str] = Field(None, max_length=500)
    college: Optional[str] = Field(None, max_length=255)
    degree: Optional[str] = Field(None, max_length=255)
    graduation_year: Optional[int] = Field(None, ge=1950, le=2040)
    country: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=100)
    notification_preference: Optional[str] = Field(None, pattern=r"^(instant|daily|weekly)$")
    onboarding_completed: Optional[bool] = None


class InterestsUpdate(BaseModel):
    """Replace all interests for a user."""

    interests: list[str] = Field(..., max_length=50)


class PreferencesUpdate(BaseModel):
    """Replace all opportunity preferences for a user."""

    opportunity_preferences: list[str] = Field(..., max_length=20)
