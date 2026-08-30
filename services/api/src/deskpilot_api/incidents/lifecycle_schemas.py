from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class IncidentTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    target: Literal["triaging", "awaiting_consent", "investigating", "awaiting_approval", "remediating", "verifying", "resolved", "escalated", "cancelled"]
    reason: str | None = Field(default=None, max_length=500)
