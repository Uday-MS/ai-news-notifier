"""Authentication service — all auth business logic.

Phase 4: Real OTP email verification, Google OAuth, login security.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.email_otp import EmailOTP
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    OTPResendRequest,
    OTPVerifyRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserResponse
from app.services.email_service import get_email_service

logger = get_logger("auth.service")

# OTP configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60


class AuthService:
    """Encapsulates all authentication business logic."""

    def __init__(self, user_repo: UserRepository, db: AsyncSession | None = None) -> None:
        self._user_repo = user_repo
        self._db = db or user_repo._db

    # ── Registration ─────────────────────────────────────────────────────

    async def register(self, data: RegisterRequest) -> UserResponse:
        """Register a new user account and send OTP email."""
        existing = await self._user_repo.get_by_email(data.email)
        if existing:
            raise ConflictError("An account with this email already exists.")

        user = await self._user_repo.create(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )

        # Generate and send OTP
        await self._generate_and_send_otp(data.email, data.full_name)

        return UserResponse.from_user(user)

    # ── Login ────────────────────────────────────────────────────────────

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate a user and return JWT tokens."""
        user = await self._user_repo.get_by_email(data.email)
        if not user:
            raise AuthenticationError("Invalid email or password.")

        if not user.hashed_password:
            raise AuthenticationError(
                "This account uses Google sign-in. Please use 'Continue with Google'."
            )

        if not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated.")

        # Phase 4: Enforce email verification
        if not user.is_verified:
            raise AuthenticationError(
                "Please verify your email first. Check your inbox for the verification code."
            )

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

        # TODO: Send reset email via email_service

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

    # ── Email Verification (Legacy Token) ────────────────────────────────

    async def verify_email(self, data: VerifyEmailRequest) -> None:
        """Verify user email using the verification token (legacy)."""
        user = await self._user_repo.get_by_verification_token(data.token)
        if not user:
            raise ValidationError("Invalid verification token.")

        await self._user_repo.update(
            user.id,
            is_verified=True,
            verification_token=None,
        )

    # ── Phase 4: OTP Email Verification ──────────────────────────────────

    async def verify_email_otp(self, data: OTPVerifyRequest) -> TokenResponse:
        """Verify email using OTP code and return JWT tokens for auto-login."""
        # Find active (non-used, non-expired) OTP for this email
        result = await self._db.execute(
            select(EmailOTP)
            .where(
                EmailOTP.email == data.email,
                EmailOTP.is_used == False,  # noqa: E712
                EmailOTP.expires_at > datetime.now(timezone.utc),
            )
            .order_by(EmailOTP.created_at.desc())
            .limit(1)
        )
        otp_record = result.scalar_one_or_none()

        if not otp_record:
            raise ValidationError("Invalid or expired verification code.")

        # Check attempt limit
        if otp_record.attempts >= OTP_MAX_ATTEMPTS:
            raise ValidationError(
                "Too many incorrect attempts. Please request a new code."
            )

        # Verify the OTP hash
        if not verify_password(data.otp_code, otp_record.otp_hash):
            otp_record.attempts += 1
            await self._db.flush()
            remaining = OTP_MAX_ATTEMPTS - otp_record.attempts
            raise ValidationError(
                f"Incorrect verification code. {remaining} attempt(s) remaining."
            )

        # OTP is valid — mark as used
        otp_record.is_used = True
        await self._db.flush()

        # Mark user as verified
        user = await self._user_repo.get_by_email(data.email)
        if not user:
            raise NotFoundError("User not found.")

        await self._user_repo.update(
            user.id,
            is_verified=True,
            verification_token=None,
        )

        # Auto-login: return JWT tokens
        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"role": user.role.value},
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def resend_otp(self, data: OTPResendRequest) -> None:
        """Resend OTP email with cooldown enforcement."""
        # Check cooldown — find most recent OTP for this email
        result = await self._db.execute(
            select(EmailOTP)
            .where(EmailOTP.email == data.email)
            .order_by(EmailOTP.created_at.desc())
            .limit(1)
        )
        recent_otp = result.scalar_one_or_none()

        if recent_otp:
            elapsed = (datetime.now(timezone.utc) - recent_otp.created_at.replace(tzinfo=timezone.utc)).total_seconds()
            if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
                wait = int(OTP_RESEND_COOLDOWN_SECONDS - elapsed)
                raise ValidationError(
                    f"Please wait {wait} seconds before requesting a new code."
                )

        # Check user exists
        user = await self._user_repo.get_by_email(data.email)
        if not user:
            # Silent return to prevent email enumeration
            return

        if user.is_verified:
            # Already verified — silent return
            return

        await self._generate_and_send_otp(data.email, user.full_name)

    async def _generate_and_send_otp(self, email: str, full_name: str = "") -> str:
        """Generate OTP, store hash, invalidate old OTPs, send email.

        Returns the plaintext OTP (for testing only — never exposed via API).
        """
        # Invalidate all existing OTPs for this email
        await self._db.execute(
            update(EmailOTP)
            .where(EmailOTP.email == email, EmailOTP.is_used == False)  # noqa: E712
            .values(is_used=True)
        )

        # Generate cryptographically secure 6-digit OTP
        otp_code = "".join(str(secrets.randbelow(10)) for _ in range(OTP_LENGTH))

        # Store hashed OTP
        otp_record = EmailOTP(
            email=email,
            otp_hash=hash_password(otp_code),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES),
            attempts=0,
            is_used=False,
        )
        self._db.add(otp_record)
        await self._db.flush()

        # Send email
        email_svc = get_email_service()
        await email_svc.send_otp(email, otp_code, full_name)

        return otp_code

    # ── Phase 4: Google OAuth ────────────────────────────────────────────

    def get_google_auth_url(self) -> str:
        """Generate Google OAuth consent URL."""
        if not settings.GOOGLE_CLIENT_ID:
            raise ValidationError("Google OAuth is not configured.")

        from google_auth_oauthlib.flow import Flow

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )

        return auth_url

    async def handle_google_callback(self, code: str) -> TokenResponse:
        """Exchange Google auth code for tokens, create/link user."""
        if not settings.GOOGLE_CLIENT_ID:
            raise ValidationError("Google OAuth is not configured.")

        from google_auth_oauthlib.flow import Flow
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        # Exchange code for tokens
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                }
            },
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

        try:
            flow.fetch_token(code=code)
        except Exception as exc:
            logger.error("Google OAuth token exchange failed: %s", exc)
            raise AuthenticationError("Google authentication failed.")

        # Verify the ID token with Google
        credentials = flow.credentials
        try:
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except Exception as exc:
            logger.error("Google ID token verification failed: %s", exc)
            raise AuthenticationError("Invalid Google identity.")

        google_sub = id_info.get("sub")
        google_email = id_info.get("email")
        google_name = id_info.get("name", "")
        email_verified = id_info.get("email_verified", False)

        if not google_sub or not google_email:
            raise AuthenticationError("Invalid Google identity data.")

        if not email_verified:
            raise AuthenticationError("Google email is not verified.")

        # Account resolution logic
        user = await self._resolve_google_user(google_sub, google_email, google_name)

        # Issue JWT tokens
        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"role": user.role.value},
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def _resolve_google_user(
        self, google_sub: str, google_email: str, google_name: str
    ):
        """Find or create user from Google identity.

        Rules:
        1. Existing user by google_id → login
        2. Existing user by email (verified) → link google_id, login
        3. Existing user by email (unverified) → link google_id, verify, login
        4. No existing user → create verified user with google_id
        """
        # Rule 1: Check by Google ID
        user = await self._user_repo.get_by_google_id(google_sub)
        if user:
            if not user.is_active:
                raise AuthenticationError("Account is deactivated.")
            return user

        # Rule 2 & 3: Check by email
        user = await self._user_repo.get_by_email(google_email)
        if user:
            if not user.is_active:
                raise AuthenticationError("Account is deactivated.")
            # Link Google ID and mark as verified
            update_fields = {"google_id": google_sub, "is_verified": True}
            if not user.full_name or user.full_name == google_email:
                update_fields["full_name"] = google_name
            await self._user_repo.update(user.id, **update_fields)
            user = await self._user_repo.get_by_id(user.id)
            return user

        # Rule 4: Create new user (no password — Google-only)
        user = await self._user_repo.create(
            email=google_email,
            hashed_password="",  # No password for Google-only users
            full_name=google_name or google_email.split("@")[0],
            google_id=google_sub,
            is_verified=True,
        )
        return user

    # ── Get Current User ─────────────────────────────────────────────────

    async def get_current_user(self, user_id: uuid.UUID) -> UserResponse:
        """Fetch the currently authenticated user."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found.")
        return UserResponse.from_user(user)
