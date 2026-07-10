"""Structured logging for the AI News Notifier application.

Provides a JSON-based structured logger that includes contextual fields
like collector name, event counts, and error details.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """Formats log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Merge any extra context passed via `extra={"context": {...}}`
        context: dict[str, Any] | None = getattr(record, "context", None)
        if context:
            log_entry["context"] = context

        if record.exc_info and record.exc_info[1]:
            log_entry["error"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, default=str)


def get_logger(name: str) -> logging.Logger:
    """Return a structured logger with the given name.

    Args:
        name: Logger name, typically the module or collector name.

    Returns:
        A configured Logger instance with structured JSON output.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, settings.COLLECTOR_LOG_LEVEL.upper(), logging.INFO))
    logger.propagate = False
    return logger
