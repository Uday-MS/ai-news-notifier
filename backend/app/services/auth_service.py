"""Authentication service — all auth business logic."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserResponse


class AuthService:
    """Encapsulates all authentication business logic."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    # ── Registration ─────────────────────────────────────────────────────

    async def register(self, data: RegisterRequest) -> UserResponse:
        """Register a new user account."""
        existing = await self._user_repo.get_by_email(data.email)
        if existing:
            raise ConflictError("An account with this email already exists.")

        verification_token = secrets.token_urlsafe(32)

        user = await self._user_repo.create(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            verification_token=verification_token,
        )

        # TODO: Send verification email (placeholder)
        # await email_service.send_verification(user.email, verification_token)

        return UserResponse.from_user(user)

    # ── Login ────────────────────────────────────────────────────────────

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate a user and return JWT tokens."""
        user = await self._user_repo.get_by_email(data.email)
        if not user:
            raise AuthenticationError("Invalid email or password.")

        if not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated.")

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"role": user.role.value},
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    # ── Token Refresh ────────────────────────────────────────────────────

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Issue a new access token from a valid refresh token."""
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise AuthenticationError("Invalid or expired refresh token.")

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type.")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload.")

        user = await self._user_repo.get_by_id(uuid.UUID(user_id))
        if not user or not user.is_active:
            raise AuthenticationError("User not found or deactivated.")

        new_access = create_access_token(
            subject=str(user.id),
            extra_claims={"role": user.role.value},
        )
        new_refresh = create_refresh_token(subject=str(user.id))

        return TokenResponse(access_token=new_access, refresh_token=new_refresh)

    # ── Forgot Password ─────────────────────────────────────────────────

    async def forgot_password(self, data: ForgotPasswordRequest) -> None:
        """Generate a password reset token."""
        user = await self._user_repo.get_by_email(data.email)
        if not user:
            # Silent return to prevent email enumeration
            return

        reset_token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(hours=1)

        await self._user_repo.update(
            user.id,
            reset_token=reset_token,
            reset_token_expires=expires,
        )

        # TODO: Send reset email (placeholder)
        # await email_service.send_password_reset(user.email, reset_token)

    # ── Reset Password ───────────────────────────────────────────────────

    async def reset_password(self, data: ResetPasswordRequest) -> None:
        """Reset password using a valid reset token."""
        user = await self._user_repo.get_by_reset_token(data.token)
        if not user:
            raise ValidationError("Invalid or expired reset token.")

        await self._user_repo.update(
            user.id,
            hashed_password=hash_password(data.new_password),
            reset_token=None,
            reset_token_expires=None,
        )

    # ── Email Verification ───────────────────────────────────────────────

    async def verify_email(self, data: VerifyEmailRequest) -> None:
        """Verify user email using the verification token."""
        user = await self._user_repo.get_by_verification_token(data.token)
        if not user:
            raise ValidationError("Invalid verification token.")

        await self._user_repo.update(
            user.id,
            is_verified=True,
            verification_token=None,
        )

    # ── Get Current User ─────────────────────────────────────────────────

    async def get_current_user(self, user_id: uuid.UUID) -> UserResponse:
        """Fetch the currently authenticated user."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")
        return UserResponse.from_user(user)
