"""Stage 3 — Tag Extraction Service.

Extracts and normalizes tags from event fields: title, summary,
organization, existing tags, and metadata.
"""

from __future__ import annotations

import re
from typing import Any


# Well-known AI/tech terms to detect as tags
_KNOWN_TAGS: list[str] = [
    # Companies / orgs
    "openai", "anthropic", "google", "deepmind", "meta", "microsoft",
    "nvidia", "apple", "amazon", "aws", "ibm", "hugging face", "huggingface",
    "stability ai", "mistral ai", "cohere", "databricks", "snowflake",
    "tesla", "baidu", "alibaba", "tencent", "intel", "amd", "qualcomm",
    # Models
    "gpt-4", "gpt-4o", "gpt-5", "claude", "gemini", "llama", "mistral",
    "phi-3", "phi-4", "qwen", "deepseek", "falcon", "vicuna", "command r",
    "stable diffusion", "dall-e", "midjourney", "sora", "whisper", "codex",
    # Frameworks / tools
    "pytorch", "tensorflow", "jax", "keras", "langchain", "llamaindex",
    "vllm", "ollama", "transformers", "diffusers", "gradio", "streamlit",
    "fastapi", "flask", "django", "react", "next.js", "docker", "kubernetes",
    # Concepts
    "llm", "nlp", "computer vision", "reinforcement learning",
    "fine-tuning", "rlhf", "rag", "retrieval augmented generation",
    "prompt engineering", "chain of thought", "cot", "agent", "agentic",
    "embedding", "vector database", "quantization", "distillation",
    "multimodal", "text-to-image", "text-to-video", "text-to-speech",
    "speech-to-text", "code generation", "api", "sdk", "open source",
    "machine learning", "deep learning", "neural network", "transformer",
    "attention", "diffusion", "generative ai", "artificial intelligence",
    # Platforms
    "github", "gitlab", "arxiv", "kaggle", "hugging face hub",
]

_WORD_SPLIT_RE = re.compile(r"[^a-z0-9.#+\-]+")


class TagService:
    """Extracts normalized tags from event content and metadata."""

    def extract_tags(
        self,
        title: str,
        summary: str,
        organization: str = "",
        existing_tags: list[str] | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        """Generate a deduplicated list of normalized tags.

        Strategy:
        1. Match known terms in title + summary + organization.
        2. Merge existing collector-provided tags.
        3. Extract repo-style tags from metadata.
        4. Deduplicate and sort.
        """
        tags: set[str] = set()

        # Combine text for matching
        combined = f"{title} {summary} {organization}".lower()

        # 1. Match known tags
        for known in _KNOWN_TAGS:
            if known in combined:
                tags.add(self._normalize_tag(known))

        # 2. Merge existing tags from collector
        if existing_tags:
            for tag in existing_tags:
                normalized = self._normalize_tag(tag)
                if normalized and len(normalized) >= 2:
                    tags.add(normalized)

        # 3. Extract from metadata
        if extra_metadata:
            repo = extra_metadata.get("repository", "")
            if repo:
                # Extract org/repo parts as tags
                parts = repo.strip("/").split("/")
                for part in parts[-2:]:  # last two segments
                    normalized = self._normalize_tag(part)
                    if normalized and len(normalized) >= 2:
                        tags.add(normalized)

            # Keywords from metadata
            kw_list = extra_metadata.get("keywords", [])
            if isinstance(kw_list, list):
                for kw in kw_list:
                    normalized = self._normalize_tag(str(kw))
                    if normalized and len(normalized) >= 2:
                        tags.add(normalized)

        # Organization as a tag
        org_tag = self._normalize_tag(organization)
        if org_tag and len(org_tag) >= 2:
            tags.add(org_tag)

        return sorted(tags)

    def _normalize_tag(self, tag: str) -> str:
        """Lowercase, strip, and clean a tag string."""
        tag = tag.lower().strip()
        # Replace internal whitespace with hyphens for multi-word tags
        tag = re.sub(r"\s+", "-", tag)
        # Remove any chars that aren't alphanumeric, dot, hash, plus, or hyphen
        tag = re.sub(r"[^a-z0-9.#+\-]", "", tag)
        # Strip leading/trailing hyphens
        tag = tag.strip("-")
        return tag
