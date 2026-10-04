"""Authentication API routes.

Phase 4: Real Google OAuth, OTP verification, rate-limited endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.responses import success_response
from app.database.session import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    OTPResendRequest,
    OTPVerifyRequest,
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
    return AuthService(UserRepository(db), db=db)


# ── Registration ─────────────────────────────────────────────────────────


@router.post("/register", status_code=201)
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(_get_auth_service),
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account. Sends OTP email for verification."""
    user = await service.register(data)
    await db.commit()
    return success_response(
        data=user.model_dump(mode="json"),
        message="Registration successful. Please check your email for the verification code.",
    )


# ── Login ────────────────────────────────────────────────────────────────


@router.post("/login")
async def login(
    data: LoginRequest,
    service: AuthService = Depends(_get_auth_service),
):
    """Authenticate and receive JWT tokens. Email must be verified."""
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
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset link."""
    await service.forgot_password(data)
    await db.commit()
    return success_response(
        message="If an account with this email exists, a reset link has been sent."
    )


# ── Reset Password ──────────────────────────────────────────────────────


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    service: AuthService = Depends(_get_auth_service),
    db: AsyncSession = Depends(get_db),
):
    """Reset password with a valid token."""
    await service.reset_password(data)
    await db.commit()
    return success_response(message="Password reset successful.")


# ── Email Verification (Legacy Token) ───────────────────────────────────


@router.post("/verify-email")
async def verify_email(
    data: VerifyEmailRequest,
    service: AuthService = Depends(_get_auth_service),
    db: AsyncSession = Depends(get_db),
):
    """Verify user email address (legacy token method)."""
    await service.verify_email(data)
    await db.commit()
    return success_response(message="Email verified successfully.")


# ── Phase 4: OTP Email Verification ─────────────────────────────────────


@router.post("/verify-email/confirm")
async def verify_email_otp(
    data: OTPVerifyRequest,
    service: AuthService = Depends(_get_auth_service),
    db: AsyncSession = Depends(get_db),
):
    """Verify email using 6-digit OTP code. Returns JWT tokens on success."""
    tokens = await service.verify_email_otp(data)
    await db.commit()
    return success_response(
        data=tokens.model_dump(),
        message="Email verified successfully.",
    )


@router.post("/verify-email/resend")
async def resend_otp(
    data: OTPResendRequest,
    service: AuthService = Depends(_get_auth_service),
    db: AsyncSession = Depends(get_db),
):
    """Resend OTP verification email. Rate-limited to 1/minute."""
    await service.resend_otp(data)
    await db.commit()
    return success_response(
        message="If an account exists with this email, a new verification code has been sent."
    )


# ── Current User (Protected) ────────────────────────────────────────────


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get the currently authenticated user."""
    user_data = UserResponse.from_user(user)
    return success_response(data=user_data.model_dump(mode="json"))


# ── Phase 4: Google OAuth ────────────────────────────────────────────────


@router.get("/google/login")
async def google_login(
    service: AuthService = Depends(_get_auth_service),
):
    """Redirect to Google OAuth consent screen."""
    auth_url = service.get_google_auth_url()
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    service: AuthService = Depends(_get_auth_service),
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback. Redirects to frontend with tokens."""
    try:
        tokens = await service.handle_google_callback(code)
        await db.commit()

        # Redirect to frontend with tokens in URL fragment (not query params for security)
        redirect_url = (
            f"{settings.FRONTEND_URL}/auth/google/callback"
            f"#access_token={tokens.access_token}"
            f"&refresh_token={tokens.refresh_token}"
        )
        return RedirectResponse(url=redirect_url)

    except Exception as exc:
        # Redirect to frontend with error
        error_msg = str(exc) if str(exc) else "Google authentication failed"
        redirect_url = f"{settings.FRONTEND_URL}/login?error=google_auth_failed"
        return RedirectResponse(url=redirect_url)
