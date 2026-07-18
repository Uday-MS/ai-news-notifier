"""Stage 6 — AI Summary Service.

Provider-independent summarization interface with a rule-based default
implementation. Designed for future LLM provider extensions.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod


class BaseSummarizer(ABC):
    """Abstract summarizer interface.

    All summarizer implementations must subclass this and implement
    the ``summarize`` method. This enables swapping providers without
    changing the pipeline.

    Future implementations:
        - OpenAISummarizer
        - ClaudeSummarizer
        - GeminiSummarizer
    """

    @abstractmethod
    async def summarize(
        self,
        title: str,
        content: str,
        organization: str = "",
        category: str = "",
    ) -> str:
        """Generate a 2–4 sentence summary of the content.

        Args:
            title: Event title.
            content: Full event content/summary text.
            organization: Source organization.
            category: AI category classification.

        Returns:
            A concise 2–4 sentence summary string.
        """


class RuleBasedSummarizer(BaseSummarizer):
    """Deterministic rule-based summarizer.

    Extracts and condenses existing content into a 2–4 sentence summary
    without any external API calls. Uses sentence extraction and
    content-aware truncation.
    """

    # Sentence boundary pattern
    _SENTENCE_RE = re.compile(
        r"(?<=[.!?])\s+(?=[A-Z])"
    )

    MAX_SENTENCES = 4
    MIN_SENTENCES = 2
    MAX_SUMMARY_LENGTH = 500

    async def summarize(
        self,
        title: str,
        content: str,
        organization: str = "",
        category: str = "",
    ) -> str:
        """Generate a summary by extracting key sentences from content."""
        if not content or not content.strip():
            return self._fallback_summary(title, organization, category)

        # Split content into sentences
        sentences = self._split_sentences(content)

        if len(sentences) <= self.MAX_SENTENCES:
            # Content is already concise — use as-is
            summary = " ".join(sentences)
        else:
            # Select the most important sentences
            selected = self._select_sentences(sentences, title)
            summary = " ".join(selected)

        # Ensure summary isn't too long
        if len(summary) > self.MAX_SUMMARY_LENGTH:
            summary = summary[: self.MAX_SUMMARY_LENGTH - 3].rsplit(" ", 1)[0] + "..."

        # Prepend context if title adds information not in the summary
        if title and title.lower() not in summary.lower():
            context = self._build_context_prefix(title, organization, category)
            if context:
                summary = f"{context} {summary}"
                # Re-check length
                if len(summary) > self.MAX_SUMMARY_LENGTH:
                    summary = (
                        summary[: self.MAX_SUMMARY_LENGTH - 3].rsplit(" ", 1)[0]
                        + "..."
                    )

        return summary.strip()

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences using regex-based boundary detection."""
        # Clean up the text first
        text = re.sub(r"\s+", " ", text).strip()
        sentences = self._SENTENCE_RE.split(text)
        # Filter out very short fragments
        return [s.strip() for s in sentences if len(s.strip()) > 15]

    def _select_sentences(self, sentences: list[str], title: str) -> list[str]:
        """Select the most important sentences for the summary.

        Strategy: first sentence (intro) + sentences most relevant
        to the title + last sentence (conclusion).
        """
        if len(sentences) <= self.MAX_SENTENCES:
            return sentences

        selected: list[str] = []

        # Always include the first sentence (usually the key info)
        selected.append(sentences[0])

        # Score remaining sentences by relevance to title
        title_words = set(title.lower().split())
        scored = []
        for i, sent in enumerate(sentences[1:-1], start=1):
            sent_words = set(sent.lower().split())
            overlap = len(title_words & sent_words)
            scored.append((overlap, i, sent))

        # Sort by relevance (descending), pick top ones
        scored.sort(key=lambda x: x[0], reverse=True)
        remaining_slots = self.MAX_SENTENCES - 2  # reserve 1 for first, 1 for last
        for _, _, sent in scored[:remaining_slots]:
            selected.append(sent)

        # Include last sentence for closure
        if sentences[-1] not in selected:
            selected.append(sentences[-1])

        return selected[: self.MAX_SENTENCES]

    def _build_context_prefix(
        self, title: str, organization: str, category: str
    ) -> str:
        """Build a brief context prefix for the summary."""
        parts: list[str] = []
        if organization:
            parts.append(organization)
        if category and category != "other":
            readable = category.replace("_", " ").title()
            parts.append(readable)

        if parts:
            return f"[{' — '.join(parts)}]"
        return ""

    def _fallback_summary(
        self, title: str, organization: str, category: str
    ) -> str:
        """Generate a minimal summary when content is empty or too short."""
        parts: list[str] = []
        if title:
            parts.append(title.rstrip(".") + ".")
        if organization:
            parts.append(f"Published by {organization}.")
        if category and category != "other":
            readable = category.replace("_", " ")
            parts.append(f"Categorized as {readable}.")
        return " ".join(parts) if parts else "No summary available."
