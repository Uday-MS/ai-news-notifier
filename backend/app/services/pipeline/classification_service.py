"""Stage 2 — Content Classification Service.

Deterministic keyword-based classification of events into AICategory values.
Uses title, summary, organization, tags, and event_type as signals.
"""

from __future__ import annotations

from app.models.processed_event import AICategory


# Keyword maps: each category has a set of trigger words/phrases.
# Checked in priority order — first match wins.
_CATEGORY_KEYWORDS: list[tuple[AICategory, list[str]]] = [
    (AICategory.SECURITY, [
        "security", "vulnerability", "cve", "exploit", "breach",
        "malware", "ransomware", "cybersecurity", "patch", "zero-day",
        "data leak", "privacy", "encryption",
    ]),
    (AICategory.FUNDING, [
        "funding", "raised", "series a", "series b", "series c", "series d",
        "seed round", "investment", "valuation", "ipo", "acquisition",
        "acquired", "venture capital", "fundraise", "million raised",
        "billion raised",
    ]),
    (AICategory.HACKATHON, [
        "hackathon", "hack day", "code jam", "coding challenge",
        "buildathon", "devpost", "hackerearth",
    ]),
    (AICategory.COMPETITION, [
        "competition", "contest", "challenge", "leaderboard", "benchmark",
        "kaggle", "prize",
    ]),
    (AICategory.INTERNSHIP, [
        "internship", "intern ", "summer program", "co-op",
        "apprenticeship", "trainee",
    ]),
    (AICategory.STUDENT_PROGRAM, [
        "student program", "scholarship", "fellowship", "gsoc",
        "google summer of code", "academic program", "university program",
        "student developer", "campus ambassador",
    ]),
    (AICategory.AI_MODEL, [
        "gpt-", "gpt4", "gpt5", "claude", "gemini", "llama", "mistral",
        "phi-", "qwen", "deepseek", "falcon", "vicuna", "command r",
        "language model", "foundation model", "multimodal model",
        "embedding model", "model release", "model weights",
        "diffusion model", "stable diffusion", "dall-e", "midjourney",
        "sora", "text-to-image", "text-to-video", "text-to-speech",
    ]),
    (AICategory.AI_RESEARCH, [
        "research paper", "arxiv", "paper:", "preprint",
        "peer review", "conference paper", "journal paper",
        "findings show", "we propose", "state-of-the-art",
        "transformer", "attention mechanism", "reinforcement learning",
        "fine-tuning", "rlhf", "distillation", "quantization",
        "neural network", "deep learning", "machine learning research",
    ]),
    (AICategory.OPEN_SOURCE, [
        "open source", "open-source", "github.com", "gitlab.com",
        "apache license", "mit license", "gpl", "repository",
        "open weights", "hugging face", "huggingface",
    ]),
    (AICategory.PRODUCT_RELEASE, [
        "launch", "released", "announcing", "introduces", "new feature",
        "update:", "version ", "v1.", "v2.", "v3.", "v4.",
        "now available", "general availability", "ga release",
        "beta release", "preview release", "sdk", "api release",
        "plugin", "integration",
    ]),
    (AICategory.STARTUP, [
        "startup", "start-up", "founded", "co-founder", "cofounder",
        "y combinator", "yc ", "techstars", "incubator", "accelerator",
    ]),
]


class ClassificationService:
    """Deterministic keyword-based event classifier."""

    def classify(
        self,
        title: str,
        summary: str,
        organization: str = "",
        tags: list[str] | None = None,
        event_type: str = "",
    ) -> AICategory:
        """Classify an event into an AICategory based on keyword matching.

        All text inputs are lowercased before matching. The first category
        whose keywords appear in any of the input fields wins.
        """
        searchable = self._build_searchable_text(
            title, summary, organization, tags or [], event_type
        )

        for category, keywords in _CATEGORY_KEYWORDS:
            for kw in keywords:
                if kw in searchable:
                    return category

        return AICategory.OTHER

    def _build_searchable_text(
        self,
        title: str,
        summary: str,
        organization: str,
        tags: list[str],
        event_type: str,
    ) -> str:
        """Combine all text fields into a single lowercased search string."""
        parts = [
            title.lower(),
            summary.lower(),
            organization.lower(),
            event_type.lower(),
        ]
        parts.extend(t.lower() for t in tags)
        return " ".join(parts)
