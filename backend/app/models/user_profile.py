"""User profile related models — interests and opportunity preferences."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserInterest(Base):
    """A single interest selected by a user."""

    __tablename__ = "user_interests"
    __table_args__ = (UniqueConstraint("user_id", "interest", name="uq_user_interest"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interest: Mapped[str] = mapped_column(String(100), nullable=False)

    user = relationship("User", back_populates="interests")

    def __repr__(self) -> str:
        return f"<UserInterest {self.interest}>"


class UserOpportunityPreference(Base):
    """A single opportunity preference selected by a user."""

    __tablename__ = "user_opportunity_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "preference", name="uq_user_opp_pref"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    preference: Mapped[str] = mapped_column(String(100), nullable=False)

    user = relationship("User", back_populates="opportunity_preferences")

    def __repr__(self) -> str:
        return f"<UserOpportunityPreference {self.preference}>"
