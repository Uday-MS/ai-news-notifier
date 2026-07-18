"""Stage 4 — Entity Extraction Service.

Pattern-based extraction of named entities: organizations, models,
frameworks, languages, repositories, products, and people.
"""

from __future__ import annotations

import re
from typing import Any


# ── Known entity dictionaries ───────────────────────────────────────────

_ORGANIZATIONS: list[str] = [
    "OpenAI", "Anthropic", "Google", "Google DeepMind", "DeepMind",
    "Meta", "Meta AI", "Microsoft", "Microsoft Research", "NVIDIA",
    "Apple", "Amazon", "AWS", "IBM", "Hugging Face", "Stability AI",
    "Mistral AI", "Cohere", "Databricks", "Snowflake", "Tesla",
    "Baidu", "Alibaba", "Tencent", "Intel", "AMD", "Qualcomm",
    "xAI", "Inflection AI", "Perplexity", "Runway", "Midjourney",
    "Adobe", "Salesforce", "Oracle", "SAP", "Palantir",
    "Scale AI", "Weights & Biases", "Anyscale", "LangChain",
    "Y Combinator", "Sequoia Capital", "Andreessen Horowitz",
]

_MODELS: list[str] = [
    "GPT-4", "GPT-4o", "GPT-4o mini", "GPT-5", "GPT-3.5",
    "Claude", "Claude 3", "Claude 3.5", "Claude Opus", "Claude Sonnet",
    "Gemini", "Gemini Pro", "Gemini Ultra", "Gemini Flash",
    "LLaMA", "LLaMA 2", "LLaMA 3", "Llama 3.1",
    "Mistral", "Mixtral", "Mistral Large", "Mistral Small",
    "Phi-3", "Phi-4", "Qwen", "Qwen2", "DeepSeek", "DeepSeek-V2",
    "Falcon", "Vicuna", "Command R", "Command R+",
    "Stable Diffusion", "SDXL", "DALL-E", "DALL-E 3",
    "Midjourney", "Sora", "Whisper", "Codex",
    "PaLM", "PaLM 2", "Chinchilla", "Gopher",
]

_FRAMEWORKS: list[str] = [
    "PyTorch", "TensorFlow", "JAX", "Keras", "scikit-learn",
    "LangChain", "LlamaIndex", "vLLM", "Ollama",
    "Transformers", "Diffusers", "Gradio", "Streamlit",
    "FastAPI", "Flask", "Django", "Ray", "Spark",
    "ONNX", "TensorRT", "Triton", "DeepSpeed", "Megatron",
    "Hugging Face Hub", "MLflow", "Kubeflow", "Weights & Biases",
]

_LANGUAGES: list[str] = [
    "Python", "JavaScript", "TypeScript", "Rust", "Go", "Java",
    "C++", "C#", "Swift", "Kotlin", "R", "Julia", "Scala",
    "Ruby", "PHP", "Dart", "Mojo", "CUDA",
]

_PRODUCTS: list[str] = [
    "ChatGPT", "Copilot", "GitHub Copilot", "Bing Chat",
    "Bard", "Gemini App", "Claude AI", "Perplexity AI",
    "Notion AI", "Grammarly", "Jasper", "Cursor",
    "Replit", "Vercel", "Supabase", "Pinecone", "Weaviate",
    "Chroma", "Qdrant", "Milvus",
]

# GitHub/GitLab repo URL pattern
_REPO_RE = re.compile(
    r"(?:https?://)?(?:github|gitlab)\.com/([a-zA-Z0-9\-_.]+/[a-zA-Z0-9\-_.]+)"
)

# Simple person pattern: "CEO John Smith" / "founder Jane Doe"
# Only captures when preceded by a role indicator
_PERSON_ROLES = [
    "ceo", "cto", "coo", "founder", "co-founder", "cofounder",
    "director", "vp", "president", "chief", "researcher", "professor",
    "scientist", "engineer", "author",
]


class EntityService:
    """Pattern-based entity extraction from event text."""

    def extract_entities(
        self,
        title: str,
        summary: str,
        organization: str = "",
        extra_metadata: dict[str, Any] | None = None,
    ) -> dict[str, list[str]]:
        """Extract entities from event fields, grouped by type.

        Returns a dict with keys: organizations, models, frameworks,
        languages, repositories, products, people.
        """
        combined = f"{title} {summary} {organization}"
        metadata = extra_metadata or {}

        entities: dict[str, list[str]] = {
            "organizations": self._match_known(combined, _ORGANIZATIONS),
            "models": self._match_known(combined, _MODELS),
            "frameworks": self._match_known(combined, _FRAMEWORKS),
            "languages": self._match_known(combined, _LANGUAGES),
            "products": self._match_known(combined, _PRODUCTS),
            "repositories": self._extract_repos(combined, metadata),
            "people": self._extract_people(combined),
        }

        # Add organization field itself if not already present
        if organization.strip():
            org_lower = organization.lower()
            existing = [e.lower() for e in entities["organizations"]]
            if org_lower not in existing:
                entities["organizations"].append(organization.strip())

        return entities

    def _match_known(self, text: str, known_list: list[str]) -> list[str]:
        """Find known entities in text using case-insensitive matching."""
        found: list[str] = []
        text_lower = text.lower()
        for entity in known_list:
            if entity.lower() in text_lower:
                if entity not in found:
                    found.append(entity)
        return found

    def _extract_repos(self, text: str, metadata: dict[str, Any]) -> list[str]:
        """Extract repository references from text and metadata."""
        repos: set[str] = set()

        # From text (URLs)
        for match in _REPO_RE.finditer(text):
            repos.add(match.group(1))

        # From metadata
        repo_field = metadata.get("repository", "")
        if repo_field:
            repo_match = _REPO_RE.search(repo_field)
            if repo_match:
                repos.add(repo_match.group(1))
            elif "/" in repo_field:
                repos.add(repo_field.strip("/"))

        return sorted(repos)

    def _extract_people(self, text: str) -> list[str]:
        """Extract people names when preceded by role indicators.

        Only captures explicitly mentioned people to avoid false positives.
        The name portion must be Title Case (capitalized first letter,
        lowercase rest) to avoid matching verbs or other words.
        """
        people: list[str] = []

        for role in _PERSON_ROLES:
            # Role is case-insensitive, but name capture is case-sensitive:
            # only match 2-3 words starting with uppercase followed by lowercase
            role_pattern = re.compile(
                rf"\b{re.escape(role)}\b\s+",
                re.IGNORECASE,
            )
            for role_match in role_pattern.finditer(text):
                after = text[role_match.end():]
                name_match = re.match(
                    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})", after
                )
                if name_match:
                    name = name_match.group(1).strip()
                    if name not in people and len(name) > 3:
                        people.append(name)

        return people

