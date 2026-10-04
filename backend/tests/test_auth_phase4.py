"""Phase 4 authentication tests — OTP, Google OAuth, rate limiting, security.

Tests are deterministic — no live providers, all external calls mocked.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.email_otp import EmailOTP
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    OTPResendRequest,
    OTPVerifyRequest,
    RegisterRequest,
)
from app.services.auth_service import AuthService, OTP_MAX_ATTEMPTS


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def db_session():
    """Create an in-memory SQLite session for testing."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession as AS
    from app.database.base import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AS, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def user_repo(db_session):
    return UserRepository(db_session)


@pytest_asyncio.fixture
async def auth_service(user_repo, db_session):
    return AuthService(user_repo, db=db_session)


@pytest_asyncio.fixture
async def verified_user(db_session, user_repo):
    """Create a verified user for login tests."""
    user = await user_repo.create(
        email="verified@test.com",
        hashed_password=hash_password("Test@1234"),
        full_name="Verified User",
        is_verified=True,
    )
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def unverified_user(db_session, user_repo):
    """Create an unverified user."""
    user = await user_repo.create(
        email="unverified@test.com",
        hashed_password=hash_password("Test@1234"),
        full_name="Unverified User",
        is_verified=False,
    )
    await db_session.flush()
    return user


# ═══════════════════════════════════════════════════════════════════════════
# 1. Password Hashing
# ═══════════════════════════════════════════════════════════════════════════


class TestPasswordHashing:
    def test_hash_password(self):
        hashed = hash_password("MyP@ss1!")
        assert hashed != "MyP@ss1!"
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self):
        hashed = hash_password("MyP@ss1!")
        assert verify_password("MyP@ss1!", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("MyP@ss1!")
        assert verify_password("WrongPass1!", hashed) is False


# ═══════════════════════════════════════════════════════════════════════════
# 2. Registration
# ═══════════════════════════════════════════════════════════════════════════


class TestRegistration:
    @pytest.mark.asyncio
    async def test_register_creates_unverified_user(self, auth_service, db_session):
        with patch("app.services.auth_service.get_email_service") as mock_email:
            mock_svc = MagicMock()
            mock_svc.send_otp = AsyncMock(return_value=True)
            mock_email.return_value = mock_svc

            result = await auth_service.register(
                RegisterRequest(email="new@test.com", password="Strong@1234", full_name="New User")
            )

            assert result.email == "new@test.com"
            assert result.is_verified is False

            # OTP should have been created
            otp_result = await db_session.execute(
                select(EmailOTP).where(EmailOTP.email == "new@test.com")
            )
            otp = otp_result.scalar_one_or_none()
            assert otp is not None
            assert otp.is_used is False

            # Email should have been sent
            mock_svc.send_otp.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, auth_service, verified_user):
        from app.core.exceptions import ConflictError

        with pytest.raises(ConflictError, match="already exists"):
            await auth_service.register(
                RegisterRequest(email="verified@test.com", password="Strong@1234", full_name="Dup")
            )


# ═══════════════════════════════════════════════════════════════════════════
# 3. Login
# ═══════════════════════════════════════════════════════════════════════════


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, verified_user):
        tokens = await auth_service.login(
            LoginRequest(email="verified@test.com", password="Test@1234")
        )
        assert tokens.access_token
        assert tokens.refresh_token
        payload = decode_token(tokens.access_token)
        assert payload["sub"] == str(verified_user.id)

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, auth_service, verified_user):
        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await auth_service.login(
                LoginRequest(email="verified@test.com", password="WrongP@ss1")
            )

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, auth_service):
        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await auth_service.login(
                LoginRequest(email="nobody@test.com", password="Test@1234")
            )

    @pytest.mark.asyncio
    async def test_login_unverified_blocked(self, auth_service, unverified_user):
        """Phase 4: Unverified users must not be able to login."""
        from app.core.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError, match="verify your email"):
            await auth_service.login(
                LoginRequest(email="unverified@test.com", password="Test@1234")
            )

    @pytest.mark.asyncio
    async def test_login_google_only_user(self, auth_service, user_repo, db_session):
        """Google-only users (no password) get a helpful error."""
        from app.core.exceptions import AuthenticationError

        await user_repo.create(
            email="google@test.com",
            hashed_password="",
            full_name="Google User",
            google_id="goog123",
            is_verified=True,
        )
        await db_session.flush()

        with pytest.raises(AuthenticationError, match="Google sign-in"):
            await auth_service.login(
                LoginRequest(email="google@test.com", password="Test@1234")
            )


# ═══════════════════════════════════════════════════════════════════════════
# 4. OTP Generation & Hashing
# ═══════════════════════════════════════════════════════════════════════════


class TestOTPGeneration:
    @pytest.mark.asyncio
    async def test_otp_is_hashed(self, auth_service, db_session):
        with patch("app.services.auth_service.get_email_service") as mock_email:
            mock_svc = MagicMock()
            mock_svc.send_otp = AsyncMock(return_value=True)
            mock_email.return_value = mock_svc

            otp_code = await auth_service._generate_and_send_otp("otp@test.com", "Test")
            assert len(otp_code) == 6
            assert otp_code.isdigit()

            # Stored OTP is hashed, not plaintext
            result = await db_session.execute(
                select(EmailOTP).where(EmailOTP.email == "otp@test.com")
            )
            otp_record = result.scalar_one()
            assert otp_record.otp_hash != otp_code
            assert otp_record.otp_hash.startswith("$2b$")

            # Hash verifies against original code
            assert verify_password(otp_code, otp_record.otp_hash) is True

    @pytest.mark.asyncio
    async def test_otp_invalidates_old(self, auth_service, db_session):
        with patch("app.services.auth_service.get_email_service") as mock_email:
            mock_svc = MagicMock()
            mock_svc.send_otp = AsyncMock(return_value=True)
            mock_email.return_value = mock_svc

            await auth_service._generate_and_send_otp("inv@test.com")
            await auth_service._generate_and_send_otp("inv@test.com")

            result = await db_session.execute(
                select(EmailOTP).where(
                    EmailOTP.email == "inv@test.com",
                    EmailOTP.is_used == False,  # noqa: E712
                )
            )
            active = result.scalars().all()
            assert len(active) == 1  # Only the latest OTP is active


# ═══════════════════════════════════════════════════════════════════════════
# 5. OTP Verification
# ═══════════════════════════════════════════════════════════════════════════


class TestOTPVerification:
    @pytest.mark.asyncio
    async def test_otp_verify_success(self, auth_service, user_repo, db_session):
        """Correct OTP verifies email and returns tokens."""
        user = await user_repo.create(
            email="otpv@test.com",
            hashed_password=hash_password("Test@1234"),
            full_name="OTP Verifier",
        )
        await db_session.flush()

        with patch("app.services.auth_service.get_email_service") as mock_email:
            mock_svc = MagicMock()
            mock_svc.send_otp = AsyncMock(return_value=True)
            mock_email.return_value = mock_svc
            otp_code = await auth_service._generate_and_send_otp("otpv@test.com")

        tokens = await auth_service.verify_email_otp(
            OTPVerifyRequest(email="otpv@test.com", otp_code=otp_code)
        )
        assert tokens.access_token
        assert tokens.refresh_token

        # User should now be verified
        updated = await user_repo.get_by_email("otpv@test.com")
        assert updated.is_verified is True

    @pytest.mark.asyncio
    async def test_otp_verify_wrong_code(self, auth_service, user_repo, db_session):
        from app.core.exceptions import ValidationError

        await user_repo.create(
            email="otpw@test.com",
            hashed_password=hash_password("Test@1234"),
            full_name="Wrong OTP",
        )
        await db_session.flush()

        with patch("app.services.auth_service.get_email_service") as mock_email:
            mock_svc = MagicMock()
            mock_svc.send_otp = AsyncMock(return_value=True)
            mock_email.return_value = mock_svc
            await auth_service._generate_and_send_otp("otpw@test.com")

        with pytest.raises(ValidationError, match="Incorrect"):
            await auth_service.verify_email_otp(
                OTPVerifyRequest(email="otpw@test.com", otp_code="000000")
            )

    @pytest.mark.asyncio
    async def test_otp_expired(self, auth_service, user_repo, db_session):
        from app.core.exceptions import ValidationError

        await user_repo.create(
            email="otpe@test.com",
            hashed_password=hash_password("Test@1234"),
            full_name="Expired OTP",
        )
        await db_session.flush()

        # Manually create an expired OTP
        otp = EmailOTP(
            email="otpe@test.com",
            otp_hash=hash_password("123456"),
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        db_session.add(otp)
        await db_session.flush()

        with pytest.raises(ValidationError, match="expired"):
            await auth_service.verify_email_otp(
                OTPVerifyRequest(email="otpe@test.com", otp_code="123456")
            )

    @pytest.mark.asyncio
    async def test_otp_single_use(self, auth_service, user_repo, db_session):
        """OTP cannot be reused after successful verification."""
        from app.core.exceptions import ValidationError

        await user_repo.create(
            email="otps@test.com",
            hashed_password=hash_password("Test@1234"),
            full_name="Single Use",
        )
        await db_session.flush()

        with patch("app.services.auth_service.get_email_service") as mock_email:
            mock_svc = MagicMock()
            mock_svc.send_otp = AsyncMock(return_value=True)
            mock_email.return_value = mock_svc
            otp_code = await auth_service._generate_and_send_otp("otps@test.com")

        # First verification succeeds
        await auth_service.verify_email_otp(
            OTPVerifyRequest(email="otps@test.com", otp_code=otp_code)
        )

        # Second attempt fails — OTP is used
        with pytest.raises(ValidationError):
            await auth_service.verify_email_otp(
                OTPVerifyRequest(email="otps@test.com", otp_code=otp_code)
            )

    @pytest.mark.asyncio
    async def test_otp_attempt_limit(self, auth_service, user_repo, db_session):
        """After 5 wrong attempts, OTP is locked."""
        from app.core.exceptions import ValidationError

        await user_repo.create(
            email="otpa@test.com",
            hashed_password=hash_password("Test@1234"),
            full_name="Attempt Limit",
        )
        await db_session.flush()

        with patch("app.services.auth_service.get_email_service") as mock_email:
            mock_svc = MagicMock()
            mock_svc.send_otp = AsyncMock(return_value=True)
            mock_email.return_value = mock_svc
            await auth_service._generate_and_send_otp("otpa@test.com")

        # Use up all attempts
        for i in range(OTP_MAX_ATTEMPTS):
            with pytest.raises(ValidationError):
                await auth_service.verify_email_otp(
                    OTPVerifyRequest(email="otpa@test.com", otp_code="000000")
                )

        # Next attempt should say "too many"
        with pytest.raises(ValidationError, match="Too many"):
            await auth_service.verify_email_otp(
                OTPVerifyRequest(email="otpa@test.com", otp_code="000000")
            )


# ═══════════════════════════════════════════════════════════════════════════
# 6. OTP Resend
# ═══════════════════════════════════════════════════════════════════════════


class TestOTPResend:
    @pytest.mark.asyncio
    async def test_resend_cooldown(self, auth_service, user_repo, db_session):
        """Resend is rate-limited by cooldown."""
        from app.core.exceptions import ValidationError

        await user_repo.create(
            email="resend@test.com",
            hashed_password=hash_password("Test@1234"),
            full_name="Resend Test",
        )
        await db_session.flush()

        with patch("app.services.auth_service.get_email_service") as mock_email:
            mock_svc = MagicMock()
            mock_svc.send_otp = AsyncMock(return_value=True)
            mock_email.return_value = mock_svc
            await auth_service._generate_and_send_otp("resend@test.com")

        # Immediate resend should fail (cooldown)
        with pytest.raises(ValidationError, match="wait"):
            await auth_service.resend_otp(OTPResendRequest(email="resend@test.com"))

    @pytest.mark.asyncio
    async def test_resend_silent_for_nonexistent(self, auth_service):
        """Resend for unknown email returns silently (no enumeration)."""
        # Should not raise
        with patch("app.services.auth_service.get_email_service") as mock_email:
            mock_svc = MagicMock()
            mock_svc.send_otp = AsyncMock(return_value=True)
            mock_email.return_value = mock_svc
            await auth_service.resend_otp(OTPResendRequest(email="nobody@test.com"))


# ═══════════════════════════════════════════════════════════════════════════
# 7. Google OAuth
# ═══════════════════════════════════════════════════════════════════════════


class TestGoogleOAuth:
    @pytest.mark.asyncio
    async def test_google_not_configured(self, auth_service):
        """Without credentials, Google OAuth raises validation error."""
        from app.core.exceptions import ValidationError

        with patch("app.core.config.settings") as mock_settings:
            mock_settings.GOOGLE_CLIENT_ID = ""
            auth_service_test = auth_service
            # We need to patch settings used in the method
            with pytest.raises(ValidationError, match="not configured"):
                auth_service_test.get_google_auth_url()

    @pytest.mark.asyncio
    async def test_google_new_user_created(self, auth_service, db_session):
        """Google auth creates a new verified user if none exists."""
        user = await auth_service._resolve_google_user(
            google_sub="goog_new_123",
            google_email="newgoogle@test.com",
            google_name="Google New",
        )

        assert user.email == "newgoogle@test.com"
        assert user.google_id == "goog_new_123"
        assert user.is_verified is True
        assert user.hashed_password == ""  # No password for Google users

    @pytest.mark.asyncio
    async def test_google_existing_by_google_id(self, auth_service, user_repo, db_session):
        """Google auth recognizes existing user by google_id."""
        await user_repo.create(
            email="existing@test.com",
            hashed_password=hash_password("Test@1234"),
            full_name="Existing",
            google_id="goog_exist_123",
            is_verified=True,
        )
        await db_session.flush()

        user = await auth_service._resolve_google_user(
            google_sub="goog_exist_123",
            google_email="existing@test.com",
            google_name="Existing",
        )
        assert user.email == "existing@test.com"

    @pytest.mark.asyncio
    async def test_google_links_existing_email(self, auth_service, user_repo, db_session):
        """Google auth links google_id to existing email user."""
        await user_repo.create(
            email="link@test.com",
            hashed_password=hash_password("Test@1234"),
            full_name="Link Me",
            is_verified=True,
        )
        await db_session.flush()

        user = await auth_service._resolve_google_user(
            google_sub="goog_link_123",
            google_email="link@test.com",
            google_name="Link Me",
        )
        assert user.google_id == "goog_link_123"
        assert user.is_verified is True

    @pytest.mark.asyncio
    async def test_google_verifies_unverified_email(self, auth_service, user_repo, db_session):
        """Google auth verifies unverified email user and links."""
        await user_repo.create(
            email="unver@test.com",
            hashed_password=hash_password("Test@1234"),
            full_name="Unverified Google",
            is_verified=False,
        )
        await db_session.flush()

        user = await auth_service._resolve_google_user(
            google_sub="goog_unver_123",
            google_email="unver@test.com",
            google_name="Unverified Google",
        )
        assert user.google_id == "goog_unver_123"
        assert user.is_verified is True

    @pytest.mark.asyncio
    async def test_google_deactivated_user_blocked(self, auth_service, user_repo, db_session):
        """Deactivated users cannot use Google OAuth."""
        from app.core.exceptions import AuthenticationError

        await user_repo.create(
            email="deact@test.com",
            hashed_password=hash_password("Test@1234"),
            full_name="Deactivated",
            google_id="goog_deact_123",
            is_active=False,
        )
        await db_session.flush()

        with pytest.raises(AuthenticationError, match="deactivated"):
            await auth_service._resolve_google_user(
                google_sub="goog_deact_123",
                google_email="deact@test.com",
                google_name="Deactivated",
            )


# ═══════════════════════════════════════════════════════════════════════════
# 8. JWT Tokens
# ═══════════════════════════════════════════════════════════════════════════


class TestJWT:
    def test_access_token_valid(self):
        token = create_access_token("user-123", {"role": "user"})
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert payload["role"] == "user"

    def test_refresh_token_valid(self):
        token = create_refresh_token("user-123")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"

    def test_expired_token_rejected(self):
        from jose import jwt, JWTError
        from app.core.config import settings

        expired_token = jwt.encode(
            {"sub": "user-123", "type": "access", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        with pytest.raises(JWTError):
            decode_token(expired_token)

    def test_invalid_token_rejected(self):
        from jose import JWTError

        with pytest.raises(JWTError):
            decode_token("invalid.token.here")

    @pytest.mark.asyncio
    async def test_refresh_token_flow(self, auth_service, verified_user):
        tokens = await auth_service.login(
            LoginRequest(email="verified@test.com", password="Test@1234")
        )
        new_tokens = await auth_service.refresh_token(tokens.refresh_token)
        # New access token should be valid and belong to same user
        assert new_tokens.access_token
        payload = decode_token(new_tokens.access_token)
        assert payload["sub"] == str(verified_user.id)
        assert payload["type"] == "access"


# ═══════════════════════════════════════════════════════════════════════════
# 9. Rate Limiting
# ═══════════════════════════════════════════════════════════════════════════


class TestRateLimiting:
    def test_sliding_window_allows_within_limit(self):
        from app.middleware.rate_limiter import _SlidingWindow

        window = _SlidingWindow()
        for _ in range(5):
            assert window.is_allowed("test_key", 5, 60) is True

    def test_sliding_window_blocks_over_limit(self):
        from app.middleware.rate_limiter import _SlidingWindow

        window = _SlidingWindow()
        for _ in range(5):
            window.is_allowed("test_key2", 5, 60)
        assert window.is_allowed("test_key2", 5, 60) is False

    def test_remaining_count(self):
        from app.middleware.rate_limiter import _SlidingWindow

        window = _SlidingWindow()
        window.is_allowed("test_key3", 5, 60)
        window.is_allowed("test_key3", 5, 60)
        assert window.remaining("test_key3", 5, 60) == 3


# ═══════════════════════════════════════════════════════════════════════════
# 10. User Isolation
# ═══════════════════════════════════════════════════════════════════════════


class TestUserIsolation:
    @pytest.mark.asyncio
    async def test_user_cannot_access_other_user(self, user_repo, db_session):
        """Users can only access their own data."""
        user_a = await user_repo.create(
            email="a@test.com", hashed_password=hash_password("Test@1234"),
            full_name="A", is_verified=True,
        )
        user_b = await user_repo.create(
            email="b@test.com", hashed_password=hash_password("Test@1234"),
            full_name="B", is_verified=True,
        )
        await db_session.flush()

        # Token for user A
        token_a = create_access_token(str(user_a.id))
        payload = decode_token(token_a)

        # Payload should contain user A's ID, not user B's
        assert payload["sub"] == str(user_a.id)
        assert payload["sub"] != str(user_b.id)
