from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeviceView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID
    hostname: str = Field(min_length=1, max_length=255)
    operating_system: Literal["windows_10", "windows_11"]
    edition: str | None = Field(default=None, max_length=100)
    build: str | None = Field(default=None, max_length=50)
    architecture: Literal["x64", "arm64"] | None = None
    lifecycle_status: Literal[
        "discovered", "pending_enrollment", "active", "restricted", "quarantined", "retired"
    ]
    enrollment_status: Literal["pending", "enrolled", "revoked"]
    last_seen_at: datetime | None
    version: int = Field(ge=1)


class AssignmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: UUID
    assignment_type: Literal["primary", "shared", "temporary"]
    valid_until: datetime | None = None
    expected_device_version: int = Field(ge=1)
