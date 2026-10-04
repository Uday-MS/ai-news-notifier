"""Centralized, versioned prompt template for intelligence extraction.

The prompt instructs the LLM to produce source-grounded, structured
intelligence from a collected AI event.  All prompts are kept here so
they can be versioned and updated without touching business logic.
"""

from __future__ import annotations

INTELLIGENCE_PROMPT_VERSION = "1.0"

SYSTEM_INSTRUCTION = """\
You are an AI intelligence analyst for an AI news monitoring platform.

Your job is to analyse a collected article about AI/ML developments and
produce structured intelligence that helps practitioners quickly understand
what happened and why it matters.

RULES:
1. Base ALL analysis on the provided source material only.
2. Do NOT invent facts, numbers, dates, or claims absent from the source.
3. If information is insufficient, use null or "unknown" — never hallucinate.
4. Be concise, factual, and avoid marketing language or hype.
5. The "why_it_matters" section is the most valuable part — explain significance,
   who is affected, what changed, and what technology is involved.
6. Return valid JSON matching the required schema exactly.
"""


def build_extraction_prompt(
    *,
    title: str,
    source: str,
    source_url: str,
    published_at: str,
    content: str,
) -> str:
    """Build the user prompt for a single event intelligence extraction.

    Truncates content to ~3000 chars to keep token usage efficient.
    """
    # Truncate content to avoid excessive token usage
    max_content_len = 3000
    truncated = content[:max_content_len]
    if len(content) > max_content_len:
        truncated += "... [truncated]"

    return f"""\
Analyse the following AI/ML article and produce structured intelligence.

ARTICLE DETAILS:
- Title: {title}
- Source: {source}
- URL: {source_url}
- Published: {published_at}

CONTENT:
{truncated}

REQUIRED OUTPUT (JSON):
{{
  "concise_summary": "2-3 sentence factual summary of what happened",
  "why_it_matters": "2-4 sentences: why is this significant? who is affected? what changed?",
  "category": "one of: news, research, model_release, product_release, funding, security, policy, open_source, opportunity, company_update, other",
  "subcategory": "optional finer classification or null",
  "importance_score": 0-100,
  "confidence_score": 0.0-1.0,
  "relevance_signals": ["reason1", "reason2"],
  "entities": ["person names mentioned"],
  "technologies": ["tech/frameworks mentioned"],
  "organizations": ["companies/orgs mentioned"],
  "models": ["AI model names mentioned"],
  "keywords": ["5-10 keywords"],
  "intelligence_type": "same as category"
}}

Remember: only use information present in the source material above.
If a field cannot be determined from the source, use an empty list, null, or "other" as appropriate.
"""
