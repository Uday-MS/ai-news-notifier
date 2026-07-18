"""Stage 1 — Content Cleaning Service.

Deterministic content cleaning: whitespace normalization, HTML stripping,
URL cleanup, unicode normalization, and minimum length validation.
"""

from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


# Tracking parameters to strip from URLs
_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "fbclid", "gclid", "mc_cid", "mc_eid", "msclkid", "twclid",
    "igshid", "s", "si", "feature", "app",
})

# HTML tag pattern
_HTML_TAG_RE = re.compile(r"<[^>]+>")
# Consecutive whitespace (spaces, tabs, etc.) — not newlines
_MULTI_SPACE_RE = re.compile(r"[^\S\n]+")
# Three or more consecutive newlines → two newlines
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")
# Markdown image syntax
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]+\)")
# Markdown link — keep the link text
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")

MIN_CONTENT_LENGTH = 20


@dataclass
class CleanedContent:
    """Output of the cleaning stage."""

    title: str
    summary: str
    is_valid: bool
    validation_reason: str = ""


class CleaningService:
    """Deterministic content cleaning pipeline."""

    def clean(self, title: str, summary: str, source_url: str = "") -> CleanedContent:
        """Clean title and summary text, returning structured output."""
        cleaned_title = self._clean_text(title)
        cleaned_summary = self._clean_text(summary)

        # Validate minimum content length
        if len(cleaned_title.strip()) < 3:
            return CleanedContent(
                title=cleaned_title,
                summary=cleaned_summary,
                is_valid=False,
                validation_reason="Title too short after cleaning.",
            )

        if len(cleaned_summary.strip()) < MIN_CONTENT_LENGTH:
            return CleanedContent(
                title=cleaned_title,
                summary=cleaned_summary,
                is_valid=False,
                validation_reason=(
                    f"Summary below minimum length ({MIN_CONTENT_LENGTH} chars)."
                ),
            )

        return CleanedContent(
            title=cleaned_title,
            summary=cleaned_summary,
            is_valid=True,
        )

    def clean_url(self, url: str) -> str:
        """Remove tracking parameters from a URL."""
        if not url:
            return url
        try:
            parsed = urlparse(url)
            query = parse_qs(parsed.query, keep_blank_values=False)
            filtered = {
                k: v for k, v in query.items()
                if k.lower() not in _TRACKING_PARAMS
            }
            clean_query = urlencode(filtered, doseq=True)
            return urlunparse(parsed._replace(query=clean_query))
        except Exception:
            return url

    # ── Internal helpers ─────────────────────────────────────────────────

    def _clean_text(self, text: str) -> str:
        """Apply all cleaning transformations to a text string."""
        if not text:
            return ""

        # 1. Unicode normalization (NFC form)
        text = unicodedata.normalize("NFC", text)

        # 2. Decode HTML entities
        text = html.unescape(text)

        # 3. Strip HTML tags
        text = _HTML_TAG_RE.sub("", text)

        # 4. Normalize markdown: remove images, keep link text
        text = _MD_IMAGE_RE.sub(r"\1", text)
        text = _MD_LINK_RE.sub(r"\1", text)

        # 5. Collapse duplicate whitespace
        text = _MULTI_SPACE_RE.sub(" ", text)

        # 6. Collapse excessive newlines
        text = _MULTI_NEWLINE_RE.sub("\n\n", text)

        # 7. Strip leading/trailing whitespace
        text = text.strip()

        return text
