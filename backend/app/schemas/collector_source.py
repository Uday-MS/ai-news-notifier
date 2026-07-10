"""Pydantic schemas for the CollectorSource model."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CollectorSourceCreate(BaseModel):
    """Schema for registering a new collector source."""

    name: str = Field(..., max_length=255)
    collector_type: str = Field(..., max_length=50)
    url: str = Field(..., max_length=2048)
    config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    collection_interval_minutes: int = Field(default=60, ge=1)


class CollectorSourceRead(BaseModel):
    """Full collector source representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    collector_type: str
    url: str
    config: dict[str, Any]
    is_active: bool
    last_collected_at: datetime | None
    collection_interval_minutes: int
    created_at: datetime
    updated_at: datetime


class CollectorSourceUpdate(BaseModel):
    """Partial update schema for a collector source."""

    name: str | None = None
    url: str | None = None
    config: dict[str, Any] | None = None
    is_active: bool | None = None
    collection_interval_minutes: int | None = Field(default=None, ge=1)
