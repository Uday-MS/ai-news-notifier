"""Structured API response helpers."""

from __future__ import annotations

from typing import Any


def success_response(data: Any = None, message: str | None = None) -> dict[str, Any]:
    """Return a standardised success envelope."""
    response: dict[str, Any] = {"success": True}
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return response


def error_response(code: str, message: str) -> dict[str, Any]:
    """Return a standardised error envelope."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
