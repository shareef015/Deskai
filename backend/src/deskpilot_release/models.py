from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
import json


class ProductionEvidenceStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NOT_RUN = "not_run"


class GoLiveDecision(StrEnum):
    PASS = "pass"
    BLOCKED = "blocked"
    BLOCKED_BY_STAGING = "blocked_by_staging"
    READY_FOR_HUMAN_PROMOTION = "ready_for_human_promotion"


@dataclass(frozen=True, slots=True)
class ProductionEvidenceItem:
    control_id: str
    status: ProductionEvidenceStatus
    source: str
    observed_at: str | None = None
    fingerprint: str | None = None
    approver: str | None = None
    notes: tuple[str, ...] = ()
    environment: str = "production"

    @property
    def is_real_evidence(self) -> bool:
        return bool(
            self.observed_at
            and self.fingerprint
            and self.source
            and self.source != "synthetic"
            and self.environment == "production"
        )


@dataclass(frozen=True, slots=True)
class ProductionControlRequirement:
    control_id: str
    description: str
    requires_human_approval: bool = False
    blocking: bool = True
    requires_real_evidence: bool = True


@dataclass(frozen=True, slots=True)
class FinalProductionCertificate:
    decision: GoLiveDecision
    passed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    controls_total: int
    controls_passed: int
    controls_not_run: int
    staging_passed: bool
    fingerprint: str
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        *,
        decision: GoLiveDecision,
        blockers: tuple[str, ...],
        warnings: tuple[str, ...],
        controls_total: int,
        controls_passed: int,
        controls_not_run: int,
        staging_passed: bool,
        metadata: dict[str, object] | None = None,
    ) -> "FinalProductionCertificate":
        payload = {
            "decision": decision.value,
            "blockers": sorted(set(blockers)),
            "warnings": sorted(set(warnings)),
            "controls_total": controls_total,
            "controls_passed": controls_passed,
            "controls_not_run": controls_not_run,
            "staging_passed": staging_passed,
            "metadata": metadata or {},
        }
        fingerprint = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return cls(
            decision=decision,
            passed=decision is GoLiveDecision.PASS,
            blockers=tuple(sorted(set(blockers))),
            warnings=tuple(sorted(set(warnings))),
            controls_total=controls_total,
            controls_passed=controls_passed,
            controls_not_run=controls_not_run,
            staging_passed=staging_passed,
            fingerprint=fingerprint,
            metadata=metadata or {},
        )
