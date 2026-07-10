"""GitHub Releases collector using the public GitHub REST API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.collectors.base import BaseCollector, RawItem
from app.core.config import settings
from app.models.collector_source import CollectorSource
from app.models.event import EventType
from app.schemas.event import EventCreate
from app.services.dedup_service import DeduplicationService


class GitHubCollector(BaseCollector):
    """Collects release events from GitHub repositories.

    Uses the ``/repos/{owner}/{repo}/releases`` endpoint.  An optional
    ``GITHUB_API_TOKEN`` raises the rate limit from 60 → 5 000 req/h.

    Expected ``source.config`` keys:
        - ``owner``: GitHub org or user (e.g. ``"openai"``)
        - ``repo``:  Repository name  (e.g. ``"openai-python"``)

    Alternatively, ``source.url`` can be the full API URL:
        ``https://api.github.com/repos/openai/openai-python/releases``
    """

    collector_type: str = "github"

    async def fetch(self, source: CollectorSource) -> list[RawItem]:
        """Fetch releases from the GitHub API."""
        url = self._build_url(source)
        headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
        if settings.GITHUB_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_API_TOKEN}"

        async with httpx.AsyncClient(
            timeout=settings.COLLECTOR_REQUEST_TIMEOUT
        ) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

        releases: list[dict[str, Any]] = response.json()
        items: list[RawItem] = []

        for rel in releases[: settings.COLLECTOR_MAX_ITEMS_PER_RUN]:
            items.append(
                RawItem(
                    title=rel.get("name") or rel.get("tag_name", ""),
                    summary=rel.get("body", "") or "",
                    link=rel.get("html_url", ""),
                    published=rel.get("published_at", rel.get("created_at", "")),
                    author=rel.get("author", {}).get("login", ""),
                    tags=[rel.get("tag_name", "")],
                    extra={
                        "prerelease": rel.get("prerelease", False),
                        "draft": rel.get("draft", False),
                        "tarball_url": rel.get("tarball_url", ""),
                        "repo": source.config.get("repo", ""),
                    },
                )
            )
        return items

    def normalize(self, raw: RawItem, source: CollectorSource) -> EventCreate:
        """Convert a GitHub release into a normalised EventCreate."""
        published_at = self._parse_date(raw.get("published", ""))
        source_url = raw.get("link", "")
        title = raw.get("title", "Untitled Release")

        content_hash = DeduplicationService.generate_content_hash(
            source_url, title, published_at
        )

        organization = source.config.get("owner", source.name)

        # Truncate very long release notes for the summary
        summary = raw.get("summary", "")
        if len(summary) > 2000:
            summary = summary[:1997] + "..."

        return EventCreate(
            title=title,
            summary=summary,
            source=source.name,
            source_url=source_url,
            published_at=published_at,
            event_type=EventType.RELEASE,
            organization=organization,
            tags=raw.get("tags", []),
            extra_metadata=raw.get("extra", {}),
            collector_id=self.collector_type,
            content_hash=content_hash,
        )

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _build_url(source: CollectorSource) -> str:
        """Resolve the GitHub API URL from source config or raw URL."""
        if source.url.startswith("https://api.github.com"):
            return source.url

        owner = source.config.get("owner", "")
        repo = source.config.get("repo", "")
        if owner and repo:
            return f"https://api.github.com/repos/{owner}/{repo}/releases"

        raise ValueError(
            f"GitHub source '{source.name}' has no valid API URL or owner/repo config."
        )

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """Parse ISO-8601 dates from GitHub (e.g. 2024-03-15T12:00:00Z)."""
        if not date_str:
            return datetime.now(timezone.utc)
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)
