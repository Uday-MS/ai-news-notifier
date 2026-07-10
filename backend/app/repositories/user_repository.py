"""User repository — data access layer for the User model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Handles all database operations for the User model."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> User | None:
        result = await self._db.execute(select(User).where(User.google_id == google_id))
        return result.scalar_one_or_none()

    async def get_by_verification_token(self, token: str) -> User | None:
        result = await self._db.execute(
            select(User).where(User.verification_token == token)
        )
        return result.scalar_one_or_none()

    async def get_by_reset_token(self, token: str) -> User | None:
        result = await self._db.execute(
            select(User).where(
                User.reset_token == token,
                User.reset_token_expires > datetime.utcnow(),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs: Any) -> User:
        user = User(**kwargs)
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def update(self, user_id: uuid.UUID, **kwargs: Any) -> User | None:
        await self._db.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )
        await self._db.flush()
        return await self.get_by_id(user_id)
