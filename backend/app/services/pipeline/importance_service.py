"""Stage 5 — Importance Scoring Service.

Deterministic scoring (0–100) based on source authority, content signals,
timeliness, and event type.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.models.processed_event import AICategory


# ── Scoring weights ─────────────────────────────────────────────────────

_OFFICIAL_SOURCES: set[str] = {
    "openai.com", "anthropic.com", "deepmind.google", "ai.google",
    "ai.meta.com", "blogs.microsoft.com", "developer.nvidia.com",
    "blog.google", "aws.amazon.com", "research.ibm.com",
    "huggingface.co", "stability.ai", "mistral.ai",
}

_VERIFIED_ORGS: set[str] = {
    "openai", "anthropic", "google", "google deepmind", "deepmind",
    "meta", "meta ai", "microsoft", "nvidia", "apple", "amazon",
    "aws", "ibm", "hugging face", "stability ai", "mistral ai",
    "cohere", "databricks", "xai",
}

# Category base scores
_CATEGORY_SCORES: dict[AICategory, int] = {
    AICategory.SECURITY: 15,
    AICategory.AI_MODEL: 12,
    AICategory.PRODUCT_RELEASE: 10,
    AICategory.AI_RESEARCH: 10,
    AICategory.FUNDING: 8,
    AICategory.OPEN_SOURCE: 8,
    AICategory.HACKATHON: 6,
    AICategory.COMPETITION: 6,
    AICategory.INTERNSHIP: 5,
    AICategory.STUDENT_PROGRAM: 5,
    AICategory.STARTUP: 5,
    AICategory.OTHER: 2,
}


class ImportanceService:
    """Deterministic importance scoring for processed events."""

    def score(
        self,
        title: str,
        summary: str,
        source: str,
        source_url: str,
        organization: str,
        ai_category: AICategory,
        published_at: datetime | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> tuple[int, str]:
        """Calculate importance score and explanation.

        Returns:
            (score, reason) — score is clamped to 0–100.
        """
        score = 0
        reasons: list[str] = []
        metadata = extra_metadata or {}
        combined = f"{title} {summary}".lower()

        # 1. Category base score
        cat_score = _CATEGORY_SCORES.get(ai_category, 2)
        score += cat_score
        reasons.append(f"Category ({ai_category.value}): +{cat_score}")

        # 2. Official source
        if self._is_official_source(source_url):
            score += 15
            reasons.append("Official source: +15")

        # 3. Verified organization
        if organization.lower().strip() in _VERIFIED_ORGS:
            score += 12
            reasons.append("Verified organization: +12")

        # 4. GitHub stars (if available)
        stars = metadata.get("stars", 0) or metadata.get("github_stars", 0)
        if isinstance(stars, (int, float)) and stars > 0:
            if stars >= 10000:
                score += 15
                reasons.append(f"GitHub stars ({stars:,}): +15")
            elif stars >= 1000:
                score += 10
                reasons.append(f"GitHub stars ({stars:,}): +10")
            elif stars >= 100:
                score += 5
                reasons.append(f"GitHub stars ({stars:,}): +5")

        # 5. Breaking release signals
        breaking_keywords = [
            "breaking", "major release", "v1.0", "launch",
            "general availability", "first release",
        ]
        if any(kw in combined for kw in breaking_keywords):
            score += 10
            reasons.append("Breaking release signal: +10")

        # 6. Deadline proximity
        deadline_str = metadata.get("deadline")
        if deadline_str and published_at:
            deadline_score = self._deadline_score(deadline_str)
            if deadline_score > 0:
                score += deadline_score
                reasons.append(f"Deadline proximity: +{deadline_score}")

        # 7. Funding amount signals
        funding_keywords = ["million", "billion", "$", "€", "£"]
        if ai_category == AICategory.FUNDING and any(
            kw in combined for kw in funding_keywords
        ):
            score += 8
            reasons.append("Funding with amount: +8")

        # 8. Research publication signals
        research_keywords = ["peer reviewed", "accepted at", "published in", "arxiv"]
        if any(kw in combined for kw in research_keywords):
            score += 5
            reasons.append("Research publication: +5")

        # 9. Student / opportunity signals
        if ai_category in (
            AICategory.INTERNSHIP,
            AICategory.STUDENT_PROGRAM,
            AICategory.HACKATHON,
            AICategory.COMPETITION,
        ):
            opportunity_keywords = ["apply now", "deadline", "register", "applications open"]
            if any(kw in combined for kw in opportunity_keywords):
                score += 5
                reasons.append("Active opportunity: +5")

        # 10. Security announcement urgency
        if ai_category == AICategory.SECURITY:
            urgent_keywords = ["critical", "urgent", "zero-day", "actively exploited"]
            if any(kw in combined for kw in urgent_keywords):
                score += 10
                reasons.append("Urgent security issue: +10")

        # Clamp to 0–100
        score = max(0, min(100, score))

        return score, "; ".join(reasons)

    def _is_official_source(self, source_url: str) -> bool:
        """Check if the source URL belongs to an official domain."""
        url_lower = source_url.lower()
        for domain in _OFFICIAL_SOURCES:
            if domain in url_lower:
                return True
        return False

    def _deadline_score(self, deadline_str: str) -> int:
        """Score based on how close a deadline is."""
        try:
            # Try parsing ISO format
            deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            days_until = (deadline - now).days
            if days_until < 0:
                return 0  # Past deadline
            if days_until <= 7:
                return 10  # Within a week
            if days_until <= 30:
                return 5  # Within a month
            return 2  # Future deadline
        except (ValueError, TypeError):
            return 0
