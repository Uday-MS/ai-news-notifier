"""Tests for EmailService and Resend integration.

Verifies:
1. Resend package is importable in the backend environment.
2. EmailService initializes and correctly formats parameters for Resend API.
3. EmailService handles Resend API failures gracefully (returns False, logs error without secrets).
4. No OTP or API key is exposed in logs.
5. Dev fallback works when RESEND_API_KEY is not configured.
"""

from __future__ import annotations

import io
import logging
from unittest.mock import MagicMock, patch

import pytest

from app.services.email_service import EmailService, get_email_service


@pytest.fixture
def email_log_capture():
    """Capture logs emitted by email.service."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("email.service")
    logger.addHandler(handler)
    try:
        yield stream
    finally:
        logger.removeHandler(handler)


def test_resend_dependency_importable():
    """Verify the resend package is installed and importable."""
    import resend

    assert hasattr(resend, "Emails")
    assert hasattr(resend.Emails, "send")


@pytest.mark.asyncio
async def test_email_service_sends_with_mocked_resend(email_log_capture):
    """Verify EmailService formats params with 'from' and calls resend.Emails.send."""
    with patch("app.core.config.settings.RESEND_API_KEY", "re_test_key_12345"), \
         patch("app.core.config.settings.EMAIL_FROM", "test@ainews.dev"):
        service = EmailService()
        assert service._enabled is True

        mock_send = MagicMock(return_value={"id": "email_12345"})

        with patch("resend.Emails.send", mock_send):
            result = await service.send_otp(
                to_email="user@example.com",
                otp_code="654321",
                full_name="Alice Test",
            )

        assert result is True
        mock_send.assert_called_once()
        called_params = mock_send.call_args[0][0]

        # Verify correct keys expected by Resend API
        assert called_params["from"] == "test@ainews.dev"
        assert called_params["to"] == ["user@example.com"]
        assert called_params["subject"] == "Your AI News Notifier Verification Code"
        assert "654321" in called_params["html"]
        assert "Alice Test" in called_params["html"]

        # Security checks: API key and OTP must NOT be in production logs
        log_text = email_log_capture.getvalue()
        assert "re_test_key_12345" not in log_text
        assert "654321" not in log_text


@pytest.mark.asyncio
async def test_email_service_handles_resend_failure(email_log_capture):
    """Verify EmailService handles API exceptions gracefully and returns False."""
    with patch("app.core.config.settings.RESEND_API_KEY", "re_test_key_12345"), \
         patch("app.core.config.settings.EMAIL_FROM", "test@ainews.dev"):
        service = EmailService()

        mock_send = MagicMock(side_effect=Exception("Resend API rate limit"))

        with patch("resend.Emails.send", mock_send):
            result = await service.send_otp(
                to_email="user@example.com",
                otp_code="112233",
                full_name="Bob",
            )

        assert result is False
        log_text = email_log_capture.getvalue()
        assert "Failed to send OTP email to user@example.com" in log_text
        # Security: No secret API key or OTP in logs
        assert "re_test_key_12345" not in log_text
        assert "112233" not in log_text


@pytest.mark.asyncio
async def test_email_service_dev_mode_without_key(email_log_capture):
    """Verify EmailService falls back to dev logging when RESEND_API_KEY is empty."""
    with patch("app.core.config.settings.RESEND_API_KEY", ""):
        service = EmailService()
        assert service._enabled is False

        result = await service.send_otp(
            to_email="dev@example.com",
            otp_code="999888",
            full_name="Dev User",
        )

        assert result is True
        log_text = email_log_capture.getvalue()
        assert "DEV EMAIL" in log_text


def test_get_email_service_singleton():
    """Verify get_email_service returns a singleton instance."""
    s1 = get_email_service()
    s2 = get_email_service()
    assert s1 is s2
