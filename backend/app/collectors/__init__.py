"""Collector framework package.

Provides the abstract base collector, built-in implementations
(RSS, GitHub, Blog), and a registry for type-based lookup.
"""

from app.collectors.registry import CollectorRegistry, collector_registry

__all__ = ["CollectorRegistry", "collector_registry"]
