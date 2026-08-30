from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from typing import Mapping


class IncidentDomain(StrEnum):
    OUTLOOK = "outlook"
    PRINTER = "printer"


class ExecutionState(StrEnum):
    INTAKE = "intake"
    RETRIEVING = "retrieving"
    GROUNDING = "grounding"
    ROUTING = "routing"
    DIAGNOSING = "diagnosing"
    AWAITING_APPROVAL = "awaiting_approval"
    REMEDIATING = "remediating"
    VERIFYING = "verifying"
    CLOSED = "closed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class RunContext:
    run_id: str
    tenant_id: str
    user_id: str
    session_id: str
    capabilities: frozenset[str]
    started_at: float
    deadline_at: float
    correlation_id: str

    def require_tenant(self, tenant_id: str) -> None:
        if not tenant_id or tenant_id != self.tenant_id:
            raise PermissionError("cross_tenant_context_denied")

    def require_capability(self, capability: str) -> None:
        if capability not in self.capabilities:
            raise PermissionError(f"missing_capability:{capability}")


@dataclass(frozen=True, slots=True)
class Incident:
    incident_id: str
    tenant_id: str
    domain: IncidentDomain
    title: str
    description: str
    device_id: str


@dataclass(frozen=True, slots=True)
class Citation:
    document_id: str
    chunk_id: str
    tenant_id: str
    content_hash: str


@dataclass(frozen=True, slots=True)
class Evidence:
    document_id: str
    chunk_id: str
    tenant_id: str
    text: str
    score: float
    trusted: bool = False

    @property
    def citation(self) -> Citation:
        return Citation(
            document_id=self.document_id,
            chunk_id=self.chunk_id,
            tenant_id=self.tenant_id,
            content_hash=sha256(self.text.encode("utf-8")).hexdigest(),
        )


@dataclass(frozen=True, slots=True)
class RemediationPlan:
    action: str
    tool_name: str
    resource_id: str
    reason: str
    risk: str
    requires_approval: bool = True

    @property
    def fingerprint(self) -> str:
        raw = f"{self.action}|{self.tool_name}|{self.resource_id}|{self.risk}"
        return sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ApprovalGrant:
    approval_id: str
    tenant_id: str
    session_id: str
    user_id: str
    plan_fingerprint: str
    issued_at: float
    expires_at: float


@dataclass(frozen=True, slots=True)
class ToolResult:
    tool_name: str
    tenant_id: str
    resource_id: str
    ok: bool
    payload: Mapping[str, object] = field(default_factory=dict)
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class ExecutionEvent:
    sequence: int
    state: ExecutionState
    event_type: str
    tenant_id: str
    run_id: str
    details: Mapping[str, object] = field(default_factory=dict)
