"""Email OTP model for secure email verification."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class EmailOTP(Base):
    """Stores hashed OTP codes for email verification.

    Security properties:
    - OTP stored as bcrypt hash (never plaintext)
    - 10 minute expiry
    - Max 5 verification attempts
    - Single-use (is_used flag)
    - Old OTPs invalidated on resend
    """

    __tablename__ = "email_otps"

    email: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    otp_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<EmailOTP {self.email} used={self.is_used}>"
