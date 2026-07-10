"""Pydantic schemas for the CollectedEvent model."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.event import EventType


class EventCreate(BaseModel):
    """Schema used by collectors to emit a new event into the pipeline."""

    title: str = Field(..., max_length=500)
    summary: str
    source: str = Field(..., max_length=255)
    source_url: str = Field(..., max_length=2048)
    published_at: datetime
    event_type: EventType
    organization: str = Field(..., max_length=255)
    tags: list[str] = Field(default_factory=list)
    extra_metadata: dict[str, Any] = Field(default_factory=dict)
    collector_id: str = Field(..., max_length=100)
    content_hash: str = Field(..., max_length=64)


class EventRead(BaseModel):
    """Full event representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    summary: str
    source: str
    source_url: str
    published_at: datetime
    event_type: EventType
    organization: str
    tags: list[str]
    extra_metadata: dict[str, Any]
    collector_id: str
    content_hash: str
    created_at: datetime
    updated_at: datetime


class EventSummary(BaseModel):
    """Lightweight event summary for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    source: str
    source_url: str
    published_at: datetime
    event_type: EventType
    organization: str
    tags: list[str]
