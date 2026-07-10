"""Authentication API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.database.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Wire up the auth service with its repository."""
    return AuthService(UserRepository(db))


# ── Registration ─────────────────────────────────────────────────────────


@router.post("/register", status_code=201)
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(_get_auth_service),
):
    """Register a new user account."""
    user = await service.register(data)
    return success_response(
        data=user.model_dump(mode="json"),
        message="Registration successful. Please verify your email.",
    )


# ── Login ────────────────────────────────────────────────────────────────


@router.post("/login")
async def login(
    data: LoginRequest,
    service: AuthService = Depends(_get_auth_service),
):
    """Authenticate and receive JWT tokens."""
    tokens = await service.login(data)
    return success_response(data=tokens.model_dump())


# ── Token Refresh ────────────────────────────────────────────────────────


@router.post("/refresh")
async def refresh(
    data: RefreshTokenRequest,
    service: AuthService = Depends(_get_auth_service),
):
    """Refresh an access token."""
    tokens = await service.refresh_token(data.refresh_token)
    return success_response(data=tokens.model_dump())


# ── Forgot Password ─────────────────────────────────────────────────────


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    service: AuthService = Depends(_get_auth_service),
):
    """Request a password reset link."""
    await service.forgot_password(data)
    return success_response(
        message="If an account with this email exists, a reset link has been sent."
    )


# ── Reset Password ──────────────────────────────────────────────────────


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    service: AuthService = Depends(_get_auth_service),
):
    """Reset password with a valid token."""
    await service.reset_password(data)
    return success_response(message="Password reset successful.")


# ── Email Verification ──────────────────────────────────────────────────


@router.post("/verify-email")
async def verify_email(
    data: VerifyEmailRequest,
    service: AuthService = Depends(_get_auth_service),
):
    """Verify user email address."""
    await service.verify_email(data)
    return success_response(message="Email verified successfully.")


# ── Current User (Protected) ────────────────────────────────────────────


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get the currently authenticated user."""
    user_data = UserResponse.model_validate(user)
    return success_response(data=user_data.model_dump(mode="json"))


# ── Google OAuth (Architecture Only) ─────────────────────────────────────


@router.get("/google/login")
async def google_login():
    """Redirect to Google OAuth consent screen."""
    # TODO: Implement when Google OAuth credentials are available
    return success_response(message="Google OAuth not yet configured.")


@router.get("/google/callback")
async def google_callback():
    """Handle Google OAuth callback."""
    # TODO: Implement when Google OAuth credentials are available
    return success_response(message="Google OAuth not yet configured.")
