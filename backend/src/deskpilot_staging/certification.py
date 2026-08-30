from __future__ import annotations

import json
from pathlib import Path

from .models import EvidenceItem, EvidenceStatus, ReleaseCandidateCertificate, ReleaseDecision
from .requirements import CONNECTED_STAGING_REQUIREMENTS


def prior_e2e_passed(project_root: Path) -> bool:
    path = project_root / "backend" / "demo" / "reports" / "E2E_CERTIFICATION.json"
    if not path.exists():
        return False
    payload = json.loads(path.read_text(encoding="utf-8"))
    return bool(dict(payload.get("certificate", {})).get("passed"))


class ConnectedStagingGate:
    def certify(self, *, project_root: Path, evidence: tuple[EvidenceItem, ...]) -> ReleaseCandidateCertificate:
        prior_ok = prior_e2e_passed(project_root)
        evidence_by_id = {item.control_id: item for item in evidence}
        blockers: list[str] = []
        warnings: list[str] = []
        passed = 0
        not_run = 0

        if not prior_ok:
            blockers.append("e2e_certificate_not_passing")

        required_ids = {r.control_id for r in CONNECTED_STAGING_REQUIREMENTS}
        unknown = sorted(set(evidence_by_id) - required_ids)
        warnings.extend(f"unknown_evidence:{control_id}" for control_id in unknown)

        for requirement in CONNECTED_STAGING_REQUIREMENTS:
            item = evidence_by_id.get(requirement.control_id)
            if item is None or item.status is EvidenceStatus.NOT_RUN:
                not_run += 1
                if requirement.blocking:
                    blockers.append(f"not_run:{requirement.control_id}")
                continue
            if item.status is EvidenceStatus.FAIL:
                if requirement.blocking:
                    blockers.append(f"failed:{requirement.control_id}")
                else:
                    warnings.append(f"failed:{requirement.control_id}")
                continue
            if requirement.requires_real_evidence and not item.is_real_evidence:
                blockers.append(f"non_real_evidence:{requirement.control_id}")
                continue
            if item.environment != "staging":
                blockers.append(f"wrong_environment:{requirement.control_id}")
                continue
            passed += 1

        if blockers:
            if not_run == len(CONNECTED_STAGING_REQUIREMENTS) and prior_ok:
                decision = ReleaseDecision.READY_FOR_CONNECTED_STAGING
            else:
                decision = ReleaseDecision.BLOCKED
        else:
            decision = ReleaseDecision.PASS

        return ReleaseCandidateCertificate.build(
            decision=decision,
            blockers=tuple(blockers),
            warnings=tuple(warnings),
            controls_total=len(CONNECTED_STAGING_REQUIREMENTS),
            controls_passed=passed,
            controls_not_run=not_run,
            prior_e2e_passed=prior_ok,
            metadata={
                "release_stage": "staging",
                "kind": "connected-staging-release-candidate-certification",
                "environment": "staging",
            },
        )
