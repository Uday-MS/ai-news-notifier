"""Unit tests for the AuthService."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from app.services.auth_service import AuthService


def _make_service(db: AsyncSession) -> AuthService:
    return AuthService(UserRepository(db))


@pytest.mark.asyncio
async def test_register_success(db_session: AsyncSession):
    service = _make_service(db_session)
    result = await service.register(
        RegisterRequest(email="new@test.com", password="StrongP@ss1", full_name="New User")
    )
    assert result.email == "new@test.com"
    assert result.full_name == "New User"
    assert result.is_verified is False


@pytest.mark.asyncio
async def test_register_duplicate_email(db_session: AsyncSession, test_user):
    service = _make_service(db_session)
    with pytest.raises(ConflictError):
        await service.register(
            RegisterRequest(email="test@example.com", password="StrongP@ss1", full_name="Dup")
        )


@pytest.mark.asyncio
async def test_login_success(db_session: AsyncSession, test_user):
    service = _make_service(db_session)
    result = await service.login(LoginRequest(email="test@example.com", password="StrongP@ss1"))
    assert result.access_token
    assert result.refresh_token
    assert result.token_type == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(db_session: AsyncSession, test_user):
    service = _make_service(db_session)
    with pytest.raises(AuthenticationError):
        await service.login(LoginRequest(email="test@example.com", password="WrongPass1!"))


@pytest.mark.asyncio
async def test_login_nonexistent_email(db_session: AsyncSession):
    service = _make_service(db_session)
    with pytest.raises(AuthenticationError):
        await service.login(LoginRequest(email="nope@test.com", password="StrongP@ss1"))


@pytest.mark.asyncio
async def test_refresh_token(db_session: AsyncSession, test_user):
    service = _make_service(db_session)
    tokens = await service.login(LoginRequest(email="test@example.com", password="StrongP@ss1"))
    new_tokens = await service.refresh_token(tokens.refresh_token)
    assert new_tokens.access_token
    assert new_tokens.access_token != tokens.access_token


@pytest.mark.asyncio
async def test_forgot_password_existing_user(db_session: AsyncSession, test_user):
    service = _make_service(db_session)
    # Should not raise
    await service.forgot_password(ForgotPasswordRequest(email="test@example.com"))
    # Verify token was set
    repo = UserRepository(db_session)
    user = await repo.get_by_email("test@example.com")
    assert user is not None
    assert user.reset_token is not None


@pytest.mark.asyncio
async def test_forgot_password_nonexistent_silent(db_session: AsyncSession):
    service = _make_service(db_session)
    # Should not raise (prevents email enumeration)
    await service.forgot_password(ForgotPasswordRequest(email="unknown@test.com"))


@pytest.mark.asyncio
async def test_reset_password(db_session: AsyncSession, test_user):
    service = _make_service(db_session)
    await service.forgot_password(ForgotPasswordRequest(email="test@example.com"))
    repo = UserRepository(db_session)
    user = await repo.get_by_email("test@example.com")
    assert user is not None and user.reset_token is not None

    await service.reset_password(
        ResetPasswordRequest(token=user.reset_token, new_password="NewStrong@1")
    )
    # Should login with new password
    tokens = await service.login(LoginRequest(email="test@example.com", password="NewStrong@1"))
    assert tokens.access_token


@pytest.mark.asyncio
async def test_verify_email(db_session: AsyncSession):
    service = _make_service(db_session)
    user_resp = await service.register(
        RegisterRequest(email="verify@test.com", password="StrongP@ss1", full_name="V User")
    )
    repo = UserRepository(db_session)
    user = await repo.get_by_email("verify@test.com")
    assert user is not None and user.verification_token is not None

    await service.verify_email(VerifyEmailRequest(token=user.verification_token))
    refreshed = await repo.get_by_email("verify@test.com")
    assert refreshed is not None
    assert refreshed.is_verified is True
