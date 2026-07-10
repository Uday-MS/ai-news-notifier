"""Custom exception classes for structured error handling."""

from __future__ import annotations


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed.") -> None:
        super().__init__(code="AUTHENTICATION_ERROR", message=message, status_code=401)


class AuthorizationError(AppException):
    """Raised when a user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions.") -> None:
        super().__init__(code="AUTHORIZATION_ERROR", message=message, status_code=403)


class ValidationError(AppException):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation failed.") -> None:
        super().__init__(code="VALIDATION_ERROR", message=message, status_code=422)


class NotFoundError(AppException):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(code="NOT_FOUND", message=message, status_code=404)


class ConflictError(AppException):
    """Raised when an operation conflicts with existing data."""

    def __init__(self, message: str = "Resource already exists.") -> None:
        super().__init__(code="CONFLICT", message=message, status_code=409)
