"""LLM Provider abstraction and Gemini implementation.

Provides a pluggable provider interface so the intelligence pipeline
is not tightly coupled to a single vendor.  The first (and default)
implementation uses the Google Gemini API via ``google-generativeai``.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("llm.provider")

# Global cooldown state across provider instances
_quota_exhausted_until: float | None = None


# ── Provider Abstraction ────────────────────────────────────────────────


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""


class LLMAuthenticationError(LLMProviderError):
    """API key missing or invalid."""


class LLMRateLimitError(LLMProviderError):
    """Rate limit exceeded (transient)."""


class LLMQuotaExhaustedError(LLMProviderError):
    """Daily or plan quota exhausted (non-transient).

    Indicates that the LLM provider has exhausted its request quota
    (e.g. Google Gemini Free Tier 20 RPD cap) and further calls should
    be suspended until the quota resets.
    """

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class LLMTimeoutError(LLMProviderError):
    """Request timed out."""


class LLMResponseError(LLMProviderError):
    """Malformed or unparseable response."""


def is_quota_exhausted_error(exc: Exception) -> bool:
    """Detect whether an exception represents non-transient daily quota exhaustion."""
    error_msg = str(exc).lower()
    signals = [
        "exceeded your current quota",
        "generaterequestsperday",
        "generate_content_free_tier",
        "quota metric",
        "check your plan and billing details",
        "free_tier_requests",
    ]
    if any(sig in error_msg for sig in signals):
        return True
    if "quota" in error_msg and ("429" in error_msg or "resource_exhausted" in error_msg):
        return True
    return False


def parse_retry_after(error_str: str) -> float | None:
    """Attempt to parse retry delay (in seconds) from error string."""
    text = error_str.lower()
    # Pattern: "retry after 9h39m12s" or "retry after 9h 39m" or "retry after 12s"
    hms_match = re.search(
        r"retry after\s+(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*(?:(\d+)\s*s)?",
        text,
    )
    if hms_match and any(hms_match.groups()):
        h = int(hms_match.group(1) or 0)
        m = int(hms_match.group(2) or 0)
        s = int(hms_match.group(3) or 0)
        total = h * 3600 + m * 60 + s
        if total > 0:
            return float(total)

    # Pattern: "retry_delay: 34740" or "seconds: 34740" or "retry-after: 34740"
    sec_match = re.search(
        r"(?:seconds|retry[-_]delay|retry[-_]after)[:\s]+(\d+)",
        text,
    )
    if sec_match:
        return float(sec_match.group(1))

    return None


class LLMProvider(ABC):
    """Abstract base for LLM providers.

    Subclasses implement ``_call_api`` with vendor-specific logic.
    The base class provides retry/backoff and structured output parsing.
    """

    def __init__(
        self,
        *,
        max_retries: int = 3,
        retry_backoff_base: float = 2.0,
        request_timeout: int = 30,
    ) -> None:
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self.request_timeout = request_timeout

    @classmethod
    def record_quota_exhaustion(cls, retry_after: float | None = None) -> None:
        """Record quota exhaustion and set global cooldown."""
        global _quota_exhausted_until
        cooldown = (
            retry_after
            if (retry_after is not None and retry_after > 0)
            else float(settings.LLM_QUOTA_COOLDOWN_SECONDS)
        )
        _quota_exhausted_until = time.time() + cooldown
        logger.warning(
            f"LLM quota exhausted. Global cooldown set for {cooldown:.0f}s",
            extra={"context": {"cooldown_seconds": cooldown}},
        )

    @classmethod
    def is_quota_exhausted(cls) -> bool:
        """Check if provider is in quota exhaustion cooldown."""
        global _quota_exhausted_until
        if _quota_exhausted_until is None:
            return False
        if time.time() >= _quota_exhausted_until:
            _quota_exhausted_until = None
            return False
        return True

    @classmethod
    def reset_quota_exhaustion(cls) -> None:
        """Reset quota exhaustion state."""
        global _quota_exhausted_until
        _quota_exhausted_until = None

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return a human-readable provider identifier (e.g. 'gemini')."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier being used."""

    @abstractmethod
    async def _call_api(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        """Make a single API call and return the raw text response.

        Implementations should raise the appropriate ``LLMProviderError``
        subclass on failure.
        """

    async def generate(
        self, system_prompt: str, user_prompt: str
    ) -> dict[str, Any]:
        """Call the LLM with bounded retry/backoff and parse JSON output.

        Returns:
            Parsed dict from the LLM JSON response.

        Raises:
            LLMQuotaExhaustedError: Immediately if quota cooldown is active or quota exceeded.
            LLMAuthenticationError: Immediately on auth error (no retries).
            LLMProviderError: After all retries are exhausted.
        """
        if self.is_quota_exhausted():
            remaining = int((_quota_exhausted_until or 0) - time.time())
            raise LLMQuotaExhaustedError(
                f"LLM provider is in quota cooldown (resets in ~{max(0, remaining)}s)",
                retry_after=max(0, remaining),
            )

        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                raw = await self._call_api(system_prompt, user_prompt)
                return self._parse_json(raw)
            except (LLMAuthenticationError, LLMQuotaExhaustedError):
                # Don't retry auth or daily quota exhaustion failures
                raise
            except (LLMRateLimitError, LLMTimeoutError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    wait = self.retry_backoff_base ** attempt
                    logger.warning(
                        f"LLM retry {attempt}/{self.max_retries} after {type(exc).__name__}",
                        extra={"context": {"wait_seconds": wait}},
                    )
                    await asyncio.sleep(wait)
            except LLMProviderError as exc:
                last_error = exc
                if attempt < self.max_retries:
                    wait = self.retry_backoff_base ** attempt
                    logger.warning(
                        f"LLM retry {attempt}/{self.max_retries} after error",
                        extra={"context": {"error": str(exc), "wait_seconds": wait}},
                    )
                    await asyncio.sleep(wait)

        raise LLMProviderError(
            f"All {self.max_retries} attempts failed: {last_error}"
        )

    def _parse_json(self, raw: str) -> dict[str, Any]:
        """Extract and parse JSON from the LLM response text."""
        text = raw.strip()

        # Handle markdown code fences
        if text.startswith("```"):
            # Remove opening fence (with optional language tag)
            first_newline = text.index("\n") if "\n" in text else 3
            text = text[first_newline + 1 :]
            # Remove closing fence
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMResponseError(f"Failed to parse JSON: {exc}") from exc


# ── Gemini Provider ─────────────────────────────────────────────────────


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider using ``google-generativeai``."""

    def __init__(
        self,
        *,
        api_key: str = "",
        model: str = "",
        max_retries: int | None = None,
        retry_backoff_base: float | None = None,
        request_timeout: int | None = None,
    ) -> None:
        super().__init__(
            max_retries=max_retries or settings.LLM_MAX_RETRIES,
            retry_backoff_base=retry_backoff_base or settings.LLM_RETRY_BACKOFF_BASE,
            request_timeout=request_timeout or settings.LLM_REQUEST_TIMEOUT,
        )
        self._api_key = api_key or settings.GEMINI_API_KEY
        self._model = model or settings.LLM_MODEL
        self._client = None

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def _get_client(self):
        """Lazily initialise the Gemini client."""
        if not self._api_key:
            raise LLMAuthenticationError(
                "GEMINI_API_KEY is not configured. "
                "Set it in .env or environment variables."
            )

        if self._client is None:
            import google.generativeai as genai

            genai.configure(api_key=self._api_key)
            self._client = genai.GenerativeModel(
                self._model,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": settings.LLM_MAX_TOKENS,
                    "response_mime_type": "application/json",
                },
            )
        return self._client

    async def _call_api(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        """Call Gemini API and return the text response."""
        try:
            client = self._get_client()
        except LLMAuthenticationError:
            raise

        try:
            # Combine system + user prompt (Gemini uses contents)
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Run in executor to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: client.generate_content(full_prompt),
                ),
                timeout=self.request_timeout,
            )

            if not response or not response.text:
                raise LLMResponseError("Empty response from Gemini")

            return response.text

        except asyncio.TimeoutError as exc:
            raise LLMTimeoutError(
                f"Gemini request timed out after {self.request_timeout}s"
            ) from exc
        except LLMProviderError:
            raise
        except Exception as exc:
            if is_quota_exhausted_error(exc):
                retry_after = parse_retry_after(str(exc))
                self.record_quota_exhaustion(retry_after)
                raise LLMQuotaExhaustedError(
                    f"Gemini quota exhausted: {exc}", retry_after=retry_after
                ) from exc

            error_msg = str(exc).lower()
            if "429" in error_msg or "resource_exhausted" in error_msg:
                raise LLMRateLimitError(f"Rate limited: {exc}") from exc
            if "401" in error_msg or "403" in error_msg or "api_key" in error_msg:
                raise LLMAuthenticationError(f"Auth error: {exc}") from exc
            raise LLMProviderError(f"Gemini API error: {exc}") from exc


# ── Factory ─────────────────────────────────────────────────────────────


def get_llm_provider() -> LLMProvider | None:
    """Create and return the configured LLM provider.

    Returns ``None`` if the API key is not configured, allowing the
    rest of the application to function without LLM enrichment.
    """
    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == "gemini":
        if not settings.GEMINI_API_KEY:
            logger.info(
                "GEMINI_API_KEY not configured — LLM enrichment disabled"
            )
            return None
        return GeminiProvider()
    else:
        logger.warning(
            f"Unknown LLM provider '{provider_name}' — LLM enrichment disabled"
        )
        return None
