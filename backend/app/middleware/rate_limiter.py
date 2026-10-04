"""In-memory sliding-window rate limiter for auth endpoints.

No Redis required — suitable for single-process development.
For production, swap with a Redis-backed implementation.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger("rate_limiter")


class _SlidingWindow:
    """Track request timestamps in a sliding window."""

    def __init__(self) -> None:
        # key → list of timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if a request is allowed and record it if so."""
        now = time.time()
        cutoff = now - window_seconds

        # Remove expired entries
        timestamps = self._requests[key]
        self._requests[key] = [t for t in timestamps if t > cutoff]

        if len(self._requests[key]) >= max_requests:
            return False

        self._requests[key].append(now)
        return True

    def remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        """Return how many requests remain in the current window."""
        now = time.time()
        cutoff = now - window_seconds
        active = [t for t in self._requests[key] if t > cutoff]
        return max(0, max_requests - len(active))

    def reset(self) -> None:
        """Clear all rate limit state. Used for testing."""
        self._requests.clear()


# Global rate limiter instance
rate_limiter = _SlidingWindow()


# ── Rate Limit Rules ────────────────────────────────────────────────────

RATE_LIMIT_RULES: dict[str, tuple[int, int]] = {
    # (max_requests, window_seconds)
    "POST:/api/v1/auth/login": (10, 60),
    "POST:/api/v1/auth/register": (10, 60),
    "POST:/api/v1/auth/verify-email/confirm": (10, 60),
    "POST:/api/v1/auth/verify-email/resend": (3, 60),
    "POST:/api/v1/auth/forgot-password": (5, 300),
    "GET:/api/v1/auth/google/login": (10, 60),
}


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply rate limiting to configured auth endpoints."""

    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path
        rule_key = f"{method}:{path}"

        rule = RATE_LIMIT_RULES.get(rule_key)
        if rule is None:
            return await call_next(request)

        max_requests, window_seconds = rule
        client_ip = _get_client_ip(request)
        limiter_key = f"{rule_key}:{client_ip}"

        if not rate_limiter.is_allowed(limiter_key, max_requests, window_seconds):
            remaining = rate_limiter.remaining(limiter_key, max_requests, window_seconds)
            logger.warning(
                "Rate limit exceeded: %s from %s",
                rule_key,
                client_ip,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                    },
                },
                headers={"Retry-After": str(window_seconds)},
            )

        return await call_next(request)
