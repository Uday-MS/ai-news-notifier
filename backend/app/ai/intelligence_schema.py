"""Structured output schema for LLM intelligence extraction.

Defines the Pydantic models that the LLM must return. These schemas
are used for both Gemini's structured output mode and for post-hoc
validation of the LLM response.
"""

from __future__ import annotations

import enum
from typing import Optional

from pydantic import BaseModel, Field


class IntelligenceType(str, enum.Enum):
    """Classification of the intelligence event type."""

    NEWS = "news"
    RESEARCH = "research"
    MODEL_RELEASE = "model_release"
    PRODUCT_RELEASE = "product_release"
    FUNDING = "funding"
    SECURITY = "security"
    POLICY = "policy"
    OPEN_SOURCE = "open_source"
    OPPORTUNITY = "opportunity"
    COMPANY_UPDATE = "company_update"
    OTHER = "other"


class LLMIntelligenceOutput(BaseModel):
    """Structured output expected from the LLM intelligence extraction.

    Every field has a default so that partial / malformed responses can
    still be partially captured and validated.
    """

    concise_summary: str = Field(
        default="",
        description="A 2-3 sentence factual summary of what happened.",
    )
    why_it_matters: str = Field(
        default="",
        description=(
            "2-4 sentences explaining why this development is significant, "
            "who is affected, and what changed. Do NOT repeat the summary."
        ),
    )
    category: str = Field(
        default="other",
        description=(
            "One of: news, research, model_release, product_release, funding, "
            "security, policy, open_source, opportunity, company_update, other."
        ),
    )
    subcategory: Optional[str] = Field(
        default=None,
        description="Optional finer-grained classification within the category.",
    )
    importance_score: int = Field(
        default=50,
        description="0-100 score of how important/impactful this development is.",
        ge=0,
        le=100,
    )
    confidence_score: float = Field(
        default=0.5,
        description="0.0-1.0 confidence that the analysis is accurate given available information.",
        ge=0.0,
        le=1.0,
    )
    relevance_signals: list[str] = Field(
        default_factory=list,
        description="Key reasons this is relevant to AI practitioners.",
    )
    entities: list[str] = Field(
        default_factory=list,
        description="Named people mentioned in the source.",
    )
    technologies: list[str] = Field(
        default_factory=list,
        description="Technologies, frameworks, or tools mentioned.",
    )
    organizations: list[str] = Field(
        default_factory=list,
        description="Companies or organizations mentioned.",
    )
    models: list[str] = Field(
        default_factory=list,
        description="AI/ML model names mentioned.",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="5-10 keywords capturing the core topics.",
    )
    intelligence_type: str = Field(
        default="other",
        description=(
            "Same enum as category. One of: news, research, model_release, "
            "product_release, funding, security, policy, open_source, "
            "opportunity, company_update, other."
        ),
    )


def validate_intelligence_output(data: dict) -> LLMIntelligenceOutput:
    """Validate and sanitise raw LLM output against the schema.

    Clamps scores, normalises category values, and strips obviously
    invalid fields without raising.
    """
    # Clamp importance_score
    if "importance_score" in data:
        try:
            data["importance_score"] = max(0, min(100, int(data["importance_score"])))
        except (ValueError, TypeError):
            data["importance_score"] = 50

    # Clamp confidence_score
    if "confidence_score" in data:
        try:
            data["confidence_score"] = max(0.0, min(1.0, float(data["confidence_score"])))
        except (ValueError, TypeError):
            data["confidence_score"] = 0.5

    # Normalise category
    valid_categories = {t.value for t in IntelligenceType}
    if "category" in data and data["category"] not in valid_categories:
        data["category"] = "other"
    if "intelligence_type" in data and data["intelligence_type"] not in valid_categories:
        data["intelligence_type"] = "other"

    # Ensure list fields are lists
    for list_field in (
        "relevance_signals", "entities", "technologies",
        "organizations", "models", "keywords",
    ):
        if list_field in data and not isinstance(data[list_field], list):
            data[list_field] = []

    return LLMIntelligenceOutput.model_validate(data)
