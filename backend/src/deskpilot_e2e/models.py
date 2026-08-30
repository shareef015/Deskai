from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
import json
from typing import Mapping


class DemoRole(StrEnum):
    RECRUITER = "recruiter"
    SERVICE_DESK = "service_desk_engineer"
    APPROVER = "approver"
    REVIEWER = "reviewer"


class ScenarioExpectation(StrEnum):
    CLOSED = "closed"
    RETRIAGE = "diagnosing"
    DENIED = "denied"


@dataclass(frozen=True, slots=True)
class SyntheticPersona:
    persona_id: str
    tenant_id: str
    display_name: str
    role: DemoRole
    capabilities: frozenset[str]
    synthetic: bool = True


@dataclass(frozen=True, slots=True)
class DemoScenario:
    scenario_id: str
    title: str
    domain: str
    incident_id: str
    tenant_id: str
    device_id: str
    description: str
    expected_action: str | None
    expected_final_state: ScenarioExpectation
    verification_ok: bool = True
    cross_tenant_context: bool = False
    expected_injection_block: bool = False


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    scenario_id: str
    passed: bool
    final_state: str
    route_domain: str
    action: str | None
    citation_count: int
    injection_blocked: bool
    approval_consumed: bool
    tenant_isolated: bool
    verification_ok: bool | None
    event_types: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GateStatus:
    name: str
    passed: bool
    source: str
    fingerprint: str | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReleaseBlockerReport:
    passed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    gates: tuple[GateStatus, ...]
    scenarios: tuple[ScenarioResult, ...]
    reset_verified: bool
    fingerprint: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        *,
        gates: tuple[GateStatus, ...],
        scenarios: tuple[ScenarioResult, ...],
        reset_verified: bool,
        extra_warnings: tuple[str, ...] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> "ReleaseBlockerReport":
        blockers = [f"gate:{gate.name}" for gate in gates if not gate.passed]
        blockers.extend(f"scenario:{result.scenario_id}" for result in scenarios if not result.passed)
        if not reset_verified:
            blockers.append("demo_reset")
        warnings = sorted({*extra_warnings, *(warning for gate in gates for warning in gate.warnings)})
        payload = {
            "gates": [
                {
                    "name": gate.name,
                    "passed": gate.passed,
                    "source": gate.source,
                    "fingerprint": gate.fingerprint,
                    "warnings": list(gate.warnings),
                }
                for gate in gates
            ],
            "scenarios": [
                {
                    "scenario_id": result.scenario_id,
                    "passed": result.passed,
                    "final_state": result.final_state,
                    "route_domain": result.route_domain,
                    "action": result.action,
                    "citation_count": result.citation_count,
                    "injection_blocked": result.injection_blocked,
                    "approval_consumed": result.approval_consumed,
                    "tenant_isolated": result.tenant_isolated,
                    "verification_ok": result.verification_ok,
                    "event_types": list(result.event_types),
                    "notes": list(result.notes),
                }
                for result in scenarios
            ],
            "reset_verified": reset_verified,
            "blockers": sorted(set(blockers)),
            "warnings": warnings,
            "metadata": dict(metadata or {}),
        }
        fingerprint = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
        unique_blockers = tuple(sorted(set(blockers)))
        return cls(
            passed=not unique_blockers,
            blockers=unique_blockers,
            warnings=tuple(warnings),
            gates=gates,
            scenarios=scenarios,
            reset_verified=reset_verified,
            fingerprint=fingerprint,
            metadata=dict(metadata or {}),
        )
