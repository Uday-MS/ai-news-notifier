"""Live AI source seed data — production-ready collector sources.

Registers trusted AI news sources into the collector_sources table.
Idempotent: re-running skips already-registered sources (checked by name).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.collector_source import CollectorSource

logger = get_logger("seeds.sources")


# ── Source Definitions ───────────────────────────────────────────────────

LIVE_AI_SOURCES: list[dict] = [
    # ── Official AI Organization Blogs ────────────────────────────────
    {
        "name": "openai-blog",
        "collector_type": "blog",
        "url": "https://openai.com/blog/rss.xml",
        "config": {
            "organization": "OpenAI",
            "event_type": "blog_post",
        },
        "collection_interval_minutes": 60,
    },
    {
        "name": "anthropic-news",
        "collector_type": "rss",
        "url": "https://www.anthropic.com/rss.xml",
        "config": {
            "organization": "Anthropic",
            "event_type": "news",
        },
        "collection_interval_minutes": 60,
    },
    {
        "name": "google-ai-blog",
        "collector_type": "blog",
        "url": "https://blog.google/technology/ai/rss/",
        "config": {
            "organization": "Google DeepMind",
            "event_type": "blog_post",
        },
        "collection_interval_minutes": 120,
    },
    {
        "name": "meta-ai-blog",
        "collector_type": "rss",
        "url": "https://ai.meta.com/blog/rss/",
        "config": {
            "organization": "Meta AI",
            "event_type": "blog_post",
        },
        "collection_interval_minutes": 120,
    },
    {
        "name": "huggingface-blog",
        "collector_type": "blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "config": {
            "organization": "Hugging Face",
            "event_type": "blog_post",
        },
        "collection_interval_minutes": 120,
    },
    {
        "name": "microsoft-ai-blog",
        "collector_type": "rss",
        "url": "https://blogs.microsoft.com/ai/feed/",
        "config": {
            "organization": "Microsoft AI",
            "event_type": "blog_post",
        },
        "collection_interval_minutes": 120,
    },
    {
        "name": "nvidia-ai-blog",
        "collector_type": "blog",
        "url": "https://blogs.nvidia.com/feed/",
        "config": {
            "organization": "NVIDIA",
            "event_type": "blog_post",
        },
        "collection_interval_minutes": 120,
    },
    # ── GitHub AI Project Releases ────────────────────────────────────
    {
        "name": "github-pytorch",
        "collector_type": "github",
        "url": "https://api.github.com/repos/pytorch/pytorch/releases",
        "config": {
            "owner": "pytorch",
            "repo": "pytorch",
            "organization": "Meta AI",
        },
        "collection_interval_minutes": 360,
    },
    {
        "name": "github-transformers",
        "collector_type": "github",
        "url": "https://api.github.com/repos/huggingface/transformers/releases",
        "config": {
            "owner": "huggingface",
            "repo": "transformers",
            "organization": "Hugging Face",
        },
        "collection_interval_minutes": 360,
    },
    {
        "name": "github-langchain",
        "collector_type": "github",
        "url": "https://api.github.com/repos/langchain-ai/langchain/releases",
        "config": {
            "owner": "langchain-ai",
            "repo": "langchain",
            "organization": "LangChain",
        },
        "collection_interval_minutes": 360,
    },
    # ── arXiv AI Research ─────────────────────────────────────────────
    {
        "name": "arxiv-cs-ai",
        "collector_type": "rss",
        "url": "https://export.arxiv.org/rss/cs.AI",
        "config": {
            "organization": "arXiv",
            "event_type": "research_paper",
        },
        "collection_interval_minutes": 240,
    },
    {
        "name": "arxiv-cs-lg",
        "collector_type": "rss",
        "url": "https://export.arxiv.org/rss/cs.LG",
        "config": {
            "organization": "arXiv",
            "event_type": "research_paper",
        },
        "collection_interval_minutes": 240,
    },
]


# ── Seeder Function ──────────────────────────────────────────────────────


async def seed_sources(db: AsyncSession) -> dict:
    """Register all live AI sources. Idempotent — skips existing.

    Returns:
        Summary dict with created, skipped, and total counts.
    """
    created = 0
    skipped = 0

    for source_def in LIVE_AI_SOURCES:
        # Check if already registered by name
        stmt = select(CollectorSource).where(
            CollectorSource.name == source_def["name"]
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            skipped += 1
            continue

        source = CollectorSource(
            name=source_def["name"],
            collector_type=source_def["collector_type"],
            url=source_def["url"],
            config=source_def["config"],
            is_active=True,
            collection_interval_minutes=source_def.get(
                "collection_interval_minutes", 60
            ),
        )
        db.add(source)
        created += 1

    if created > 0:
        await db.flush()

    logger.info(
        "Source seeding complete",
        extra={"context": {
            "created": created,
            "skipped": skipped,
            "total": len(LIVE_AI_SOURCES),
        }},
    )

    return {
        "created": created,
        "skipped": skipped,
        "total": len(LIVE_AI_SOURCES),
        "sources": [s["name"] for s in LIVE_AI_SOURCES],
    }
