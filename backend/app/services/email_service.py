"""Email delivery service using Resend.

Provides OTP email sending with proper error handling.
Falls back to console logging in development when RESEND_API_KEY is not set.
"""

from __future__ import annotations

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("email.service")


class EmailService:
    """Send transactional emails via Resend API."""

    def __init__(self) -> None:
        self._api_key = settings.RESEND_API_KEY
        self._from_email = settings.EMAIL_FROM
        self._enabled = bool(self._api_key)

        if not self._enabled:
            logger.warning(
                "Email service disabled: RESEND_API_KEY not configured. "
                "OTP codes will be logged to console in development."
            )

    async def send_otp(self, to_email: str, otp_code: str, full_name: str = "") -> bool:
        """Send an OTP verification email.

        Returns True if sent successfully, False otherwise.
        In development without API key, logs the OTP to console.
        """
        if not self._enabled:
            # Development fallback — log to console only
            logger.info(
                "DEV EMAIL: OTP for %s is %s (not sent — no RESEND_API_KEY)",
                to_email,
                otp_code,
            )
            return True

        try:
            import resend

            resend.api_key = self._api_key

            greeting = f"Hi {full_name}," if full_name else "Hi,"

            params = resend.Emails.SendParams(
                sender=self._from_email,
                to=[to_email],
                subject="Your AI News Notifier Verification Code",
                html=f"""
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 480px; margin: 0 auto; padding: 40px 20px;">
                    <h2 style="color: #1a1a2e; margin-bottom: 8px;">Verify your email</h2>
                    <p style="color: #666; font-size: 15px; line-height: 1.5;">{greeting}</p>
                    <p style="color: #666; font-size: 15px; line-height: 1.5;">Your verification code is:</p>
                    <div style="background: #f0f4ff; border-radius: 12px; padding: 24px; text-align: center; margin: 24px 0;">
                        <span style="font-size: 32px; font-weight: 700; letter-spacing: 8px; color: #1a1a2e;">{otp_code}</span>
                    </div>
                    <p style="color: #999; font-size: 13px;">This code expires in 10 minutes. Do not share it with anyone.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 32px 0;">
                    <p style="color: #999; font-size: 12px;">AI News Notifier — Your personalized AI intelligence feed.</p>
                </div>
                """,
            )

            email = resend.Emails.send(params)
            logger.info("OTP email sent to %s (id: %s)", to_email, email.get("id", "?"))
            return True

        except Exception as exc:
            logger.error("Failed to send OTP email to %s: %s", to_email, exc)
            return False


# Singleton
_email_service: EmailService | None = None


def get_email_service() -> EmailService:
    """Get or create the email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
