from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
import json


class EvidenceStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NOT_RUN = "not_run"


class ReleaseDecision(StrEnum):
    PASS = "pass"
    BLOCKED = "blocked"
    READY_FOR_CONNECTED_STAGING = "ready_for_connected_staging"


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    control_id: str
    status: EvidenceStatus
    source: str
    observed_at: str | None = None
    fingerprint: str | None = None
    notes: tuple[str, ...] = ()
    environment: str = "staging"

    @property
    def is_real_evidence(self) -> bool:
        return bool(self.observed_at and self.fingerprint and self.source and self.source != "synthetic")


@dataclass(frozen=True, slots=True)
class ControlRequirement:
    control_id: str
    description: str
    blocking: bool = True
    requires_real_evidence: bool = True


@dataclass(frozen=True, slots=True)
class ReleaseCandidateCertificate:
    decision: ReleaseDecision
    passed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    controls_total: int
    controls_passed: int
    controls_not_run: int
    fingerprint: str
    prior_e2e_passed: bool
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        *,
        decision: ReleaseDecision,
        blockers: tuple[str, ...],
        warnings: tuple[str, ...],
        controls_total: int,
        controls_passed: int,
        controls_not_run: int,
        prior_e2e_passed: bool,
        metadata: dict[str, object] | None = None,
    ) -> "ReleaseCandidateCertificate":
        payload = {
            "decision": decision.value,
            "blockers": sorted(blockers),
            "warnings": sorted(warnings),
            "controls_total": controls_total,
            "controls_passed": controls_passed,
            "controls_not_run": controls_not_run,
            "prior_e2e_passed": prior_e2e_passed,
            "metadata": metadata or {},
        }
        fingerprint = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return cls(
            decision=decision,
            passed=decision is ReleaseDecision.PASS,
            blockers=tuple(sorted(set(blockers))),
            warnings=tuple(sorted(set(warnings))),
            controls_total=controls_total,
            controls_passed=controls_passed,
            controls_not_run=controls_not_run,
            fingerprint=fingerprint,
            prior_e2e_passed=prior_e2e_passed,
            metadata=metadata or {},
        )
