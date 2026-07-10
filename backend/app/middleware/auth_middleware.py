"""Authentication middleware — JWT extraction and RBAC dependencies."""

from __future__ import annotations

import uuid

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_token
from app.database.session import get_db
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency: extract JWT, validate, and return the User."""
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise AuthenticationError("Invalid or expired token.")

    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type.")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload.")

    repo = UserRepository(db)
    user = await repo.get_by_id(uuid.UUID(user_id))
    if not user:
        raise AuthenticationError("User not found.")
    if not user.is_active:
        raise AuthenticationError("Account is deactivated.")

    return user


def require_role(*roles: UserRole):
    """Factory that returns a dependency requiring specific roles."""

    async def _check_role(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise AuthorizationError("Insufficient permissions for this action.")
        return user

    return _check_role
