from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


TRANSITIONS: dict[str, frozenset[str]] = {
    "discovered": frozenset({"pending_enrollment", "retired"}),
    "pending_enrollment": frozenset({"active", "restricted", "retired"}),
    "active": frozenset({"restricted", "quarantined", "retired"}),
    "restricted": frozenset({"active", "quarantined", "retired"}),
    "quarantined": frozenset({"restricted", "retired"}),
    "retired": frozenset(),
}


@dataclass(frozen=True, slots=True)
class DeviceLifecycle:
    tenant_id: UUID
    device_id: UUID
    state: str
    version: int

    def transition(self, target: str, *, expected_version: int) -> DeviceLifecycle:
        if expected_version != self.version:
            raise ValueError("device version conflict")
        if target not in TRANSITIONS.get(self.state, frozenset()):
            raise ValueError("device lifecycle transition denied")
        return DeviceLifecycle(self.tenant_id, self.device_id, target, self.version + 1)


@dataclass(frozen=True, slots=True)
class Assignment:
    tenant_id: UUID
    device_id: UUID
    user_id: UUID
    assignment_type: str
    valid_from: datetime
    valid_until: datetime | None

    def validate_for(self, tenant_id: UUID) -> None:
        if self.tenant_id != tenant_id:
            raise ValueError("assignment tenant mismatch")
        if self.assignment_type not in {"primary", "shared", "temporary"}:
            raise ValueError("unknown assignment type")
        if self.valid_until is not None and self.valid_until <= self.valid_from:
            raise ValueError("assignment validity window is invalid")
