"""Collector registry — maps collector_type strings to collector classes."""

from __future__ import annotations

from typing import Type

from app.collectors.base import BaseCollector


class CollectorRegistry:
    """Central registry for collector implementations.

    Allows dynamic lookup of collector classes by their ``collector_type``
    string, making it trivial to add new collectors without modifying
    orchestration code.
    """

    def __init__(self) -> None:
        self._collectors: dict[str, Type[BaseCollector]] = {}

    def register(self, collector_cls: Type[BaseCollector]) -> Type[BaseCollector]:
        """Register a collector class. Can also be used as a decorator."""
        self._collectors[collector_cls.collector_type] = collector_cls
        return collector_cls

    def get(self, collector_type: str) -> Type[BaseCollector] | None:
        """Return the collector class for the given type, or None."""
        return self._collectors.get(collector_type)

    def list_types(self) -> list[str]:
        """Return all registered collector type names."""
        return list(self._collectors.keys())


# ── Global registry with built-in collectors ─────────────────────────────

collector_registry = CollectorRegistry()


def _register_builtins() -> None:
    """Import and register the three built-in collectors."""
    from app.collectors.rss_collector import RSSCollector
    from app.collectors.github_collector import GitHubCollector
    from app.collectors.blog_collector import BlogCollector

    collector_registry.register(RSSCollector)
    collector_registry.register(GitHubCollector)
    collector_registry.register(BlogCollector)


_register_builtins()
