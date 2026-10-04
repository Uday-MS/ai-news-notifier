"""Live AI source seed data — production-ready collector sources.

Registers trusted AI news sources into the collector_sources table.
Idempotent: re-running skips already-registered sources (checked by name).
If a source exists but its URL has changed, the URL is updated in-place.
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

    # OpenAI — official blog RSS feed
    {
        "name": "openai-blog",
        "collector_type": "rss",
        "url": "https://openai.com/blog/rss.xml",
        "config": {
            "organization": "OpenAI",
            "event_type": "blog_post",
            "trust_tier": "primary",
        },
        "collection_interval_minutes": 60,
    },

    # Google DeepMind — official blog RSS
    {
        "name": "deepmind-blog",
        "collector_type": "blog",
        "url": "https://deepmind.google/blog/rss.xml",
        "config": {
            "organization": "Google DeepMind",
            "event_type": "blog_post",
            "trust_tier": "primary",
        },
        "collection_interval_minutes": 120,
    },

    # Google AI Blog — broader Google AI coverage
    {
        "name": "google-ai-blog",
        "collector_type": "blog",
        "url": "https://blog.google/technology/ai/rss/",
        "config": {
            "organization": "Google AI",
            "event_type": "blog_post",
            "trust_tier": "primary",
        },
        "collection_interval_minutes": 120,
    },

    # Microsoft Research — official research blog feed
    {
        "name": "microsoft-ai-blog",
        "collector_type": "rss",
        "url": "https://www.microsoft.com/en-us/research/feed/",
        "config": {
            "organization": "Microsoft Research",
            "event_type": "blog_post",
            "trust_tier": "primary",
        },
        "collection_interval_minutes": 120,
    },

    # Hugging Face — official blog feed
    {
        "name": "huggingface-blog",
        "collector_type": "blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "config": {
            "organization": "Hugging Face",
            "event_type": "blog_post",
            "trust_tier": "primary",
        },
        "collection_interval_minutes": 120,
    },

    # NVIDIA — official blog feed
    {
        "name": "nvidia-ai-blog",
        "collector_type": "blog",
        "url": "https://blogs.nvidia.com/feed/",
        "config": {
            "organization": "NVIDIA",
            "event_type": "blog_post",
            "trust_tier": "primary",
        },
        "collection_interval_minutes": 120,
    },

    # Mistral AI — official news RSS
    {
        "name": "mistral-ai-news",
        "collector_type": "rss",
        "url": "https://mistral.ai/news/rss",
        "config": {
            "organization": "Mistral AI",
            "event_type": "blog_post",
            "trust_tier": "primary",
        },
        "collection_interval_minutes": 120,
    },

    # ── Trusted AI News Publications ─────────────────────────────────

    # TechCrunch AI section
    {
        "name": "techcrunch-ai",
        "collector_type": "rss",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "config": {
            "organization": "TechCrunch",
            "event_type": "news",
            "trust_tier": "secondary",
        },
        "collection_interval_minutes": 60,
    },

    # VentureBeat AI
    {
        "name": "venturebeat-ai",
        "collector_type": "rss",
        "url": "https://venturebeat.com/category/ai/feed/",
        "config": {
            "organization": "VentureBeat",
            "event_type": "news",
            "trust_tier": "secondary",
        },
        "collection_interval_minutes": 120,
    },

    # MIT Technology Review
    {
        "name": "mit-tech-review",
        "collector_type": "rss",
        "url": "https://www.technologyreview.com/feed/",
        "config": {
            "organization": "MIT Technology Review",
            "event_type": "news",
            "trust_tier": "secondary",
        },
        "collection_interval_minutes": 120,
    },

    # The Verge — AI section
    {
        "name": "theverge-ai",
        "collector_type": "rss",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "config": {
            "organization": "The Verge",
            "event_type": "news",
            "trust_tier": "secondary",
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
            "trust_tier": "primary",
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
            "trust_tier": "primary",
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
            "trust_tier": "primary",
        },
        "collection_interval_minutes": 360,
    },
    {
        "name": "github-vllm",
        "collector_type": "github",
        "url": "https://api.github.com/repos/vllm-project/vllm/releases",
        "config": {
            "owner": "vllm-project",
            "repo": "vllm",
            "organization": "vLLM",
            "trust_tier": "primary",
        },
        "collection_interval_minutes": 360,
    },
    {
        "name": "github-ollama",
        "collector_type": "github",
        "url": "https://api.github.com/repos/ollama/ollama/releases",
        "config": {
            "owner": "ollama",
            "repo": "ollama",
            "organization": "Ollama",
            "trust_tier": "primary",
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
            "trust_tier": "primary",
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
            "trust_tier": "primary",
        },
        "collection_interval_minutes": 240,
    },
]


# ── Seeder Function ──────────────────────────────────────────────────────


async def seed_sources(db: AsyncSession) -> dict:
    """Register all live AI sources. Idempotent — skips existing.

    If a source already exists but its URL has changed in the seed data,
    the URL and config are updated in-place to keep sources current.

    Returns:
        Summary dict with created, skipped, updated, and total counts.
    """
    created = 0
    skipped = 0
    updated = 0

    for source_def in LIVE_AI_SOURCES:
        # Check if already registered by name
        stmt = select(CollectorSource).where(
            CollectorSource.name == source_def["name"]
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            # Update URL/config if changed
            needs_update = False
            if existing.url != source_def["url"]:
                existing.url = source_def["url"]
                needs_update = True
            if existing.config != source_def["config"]:
                existing.config = source_def["config"]
                needs_update = True
            # Re-enable sources that were disabled but are now in the seed list
            if not existing.is_active:
                existing.is_active = True
                needs_update = True

            if needs_update:
                updated += 1
            else:
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

    if created > 0 or updated > 0:
        await db.flush()

    logger.info(
        "Source seeding complete",
        extra={"context": {
            "created": created,
            "updated": updated,
            "skipped": skipped,
            "total": len(LIVE_AI_SOURCES),
        }},
    )

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "total": len(LIVE_AI_SOURCES),
        "sources": [s["name"] for s in LIVE_AI_SOURCES],
    }
