from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackSurface(StrEnum):
    IDENTITY = "identity"
    API = "api"
    TENANT = "tenant"
    RAG = "rag"
    AGENT = "agent"
    MCP = "mcp"
    HITL = "hitl"
    DATA = "data"
    FILE = "file"
    SUPPLY_CHAIN = "supply_chain"
    RESOURCE = "resource"


@dataclass(frozen=True, slots=True)
class AttackCase:
    attack_id: str
    title: str
    surface: AttackSurface
    severity: Severity
    framework_refs: tuple[str, ...]
    expected_control: str


@dataclass(frozen=True, slots=True)
class AttackResult:
    case: AttackCase
    blocked: bool
    control: str
    evidence: str
    leaked_sensitive_data: bool = False
    unauthorized_mutation: bool = False
    cross_tenant_exposure: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CampaignResult:
    results: tuple[AttackResult, ...]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def blocked(self) -> int:
        return sum(result.blocked for result in self.results)

    @property
    def block_rate(self) -> float:
        return 1.0 if not self.results else self.blocked / len(self.results)

    @property
    def critical_failures(self) -> tuple[str, ...]:
        return tuple(
            result.case.attack_id
            for result in self.results
            if result.case.severity is Severity.CRITICAL and not result.blocked
        )

    @property
    def high_failures(self) -> tuple[str, ...]:
        return tuple(
            result.case.attack_id
            for result in self.results
            if result.case.severity is Severity.HIGH and not result.blocked
        )


@dataclass(frozen=True, slots=True)
class SecurityCertificate:
    passed: bool
    failures: tuple[str, ...]
    warnings: tuple[str, ...]
    attack_block_rate: float
    critical_failures: tuple[str, ...]
    high_failures: tuple[str, ...]
    fingerprint: str
