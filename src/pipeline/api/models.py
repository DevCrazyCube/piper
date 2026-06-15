"""Webhook request schemas (validated by FastAPI/pydantic — bad payloads -> 422)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HealthSample(BaseModel):
    metric: str = Field(min_length=1, max_length=64)
    ts: datetime
    value: float | None = None


class IngestRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=128)
    samples: list[HealthSample] = Field(min_length=1, max_length=10_000)
