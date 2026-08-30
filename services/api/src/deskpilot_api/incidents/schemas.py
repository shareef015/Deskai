from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

IncidentCategory = Literal["outlook", "printer", "scanner", "windows_network"]


class IncidentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    requester_id: UUID
    device_id: UUID | None = None
    category: IncidentCategory
    impact_score: int = Field(ge=1, le=5)
    urgency_score: int = Field(ge=1, le=5)
    affected_user_count: int = Field(default=1, ge=1, le=100000)
    business_critical_service: bool = False
    security_or_safety_risk: bool = False
    complete_site_outage: bool = False
    summary: str = Field(min_length=1, max_length=500)


class IncidentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    summary: str | None = Field(default=None, min_length=1, max_length=500)


class IncidentView(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True, frozen=True)
    id: UUID
    requester_id: UUID
    device_id: UUID | None
    category: IncidentCategory
    status: str
    priority: int
    severity: str
    impact_score: int
    urgency_score: int
    summary: str
    version: int
    opened_at: datetime
    updated_at: datetime
    closed_at: datetime | None


class IncidentPage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    items: tuple[IncidentView, ...]
    next_cursor: str | None
