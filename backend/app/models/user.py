"""User model with RBAC role support."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserRole(str, enum.Enum):
    """User roles for RBAC."""

    USER = "user"
    ADMIN = "admin"


class User(Base):
    """User account model for authentication and authorization."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.USER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ── Profile Fields (Sprint 2) ────────────────────────────────────────
    username: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True, index=True
    )
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    profile_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    college: Mapped[str | None] = mapped_column(String(255), nullable=True)
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_timezone: Mapped[str | None] = mapped_column(
        "timezone", String(100), nullable=True
    )
    notification_preference: Mapped[str] = mapped_column(
        String(50), default="instant", nullable=False
    )
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # ── Relationships (Sprint 2) ─────────────────────────────────────────
    interests = relationship(
        "UserInterest", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    opportunity_preferences = relationship(
        "UserOpportunityPreference", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    # Email verification
    verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Password reset
    reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Google OAuth
    google_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
