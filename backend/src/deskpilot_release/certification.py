from __future__ import annotations

from pathlib import Path

from .models import FinalProductionCertificate, GoLiveDecision, ProductionEvidenceItem, ProductionEvidenceStatus
from .prerequisites import staging_connected_pass, staging_fingerprint
from .requirements import PRODUCTION_GO_LIVE_REQUIREMENTS


class FinalProductionGate:
    def certify(
        self,
        *,
        project_root: Path,
        evidence: tuple[ProductionEvidenceItem, ...],
    ) -> FinalProductionCertificate:
        staging_ok = staging_connected_pass(project_root)
        staging_fp = staging_fingerprint(project_root)
        by_id = {item.control_id: item for item in evidence}
        blockers: list[str] = []
        warnings: list[str] = []
        passed = 0
        not_run = 0

        if not staging_ok:
            blockers.append("staging_connected_certificate_not_passing")

        required_ids = {item.control_id for item in PRODUCTION_GO_LIVE_REQUIREMENTS}
        warnings.extend(f"unknown_evidence:{control_id}" for control_id in sorted(set(by_id) - required_ids))

        for requirement in PRODUCTION_GO_LIVE_REQUIREMENTS:
            item = by_id.get(requirement.control_id)
            if item is None or item.status is ProductionEvidenceStatus.NOT_RUN:
                not_run += 1
                if requirement.blocking:
                    blockers.append(f"not_run:{requirement.control_id}")
                continue
            if item.status is ProductionEvidenceStatus.FAIL:
                if requirement.blocking:
                    blockers.append(f"failed:{requirement.control_id}")
                else:
                    warnings.append(f"failed:{requirement.control_id}")
                continue
            if requirement.requires_real_evidence and not item.is_real_evidence:
                blockers.append(f"non_real_evidence:{requirement.control_id}")
                continue
            if item.environment != "production":
                blockers.append(f"wrong_environment:{requirement.control_id}")
                continue
            if requirement.requires_human_approval and not item.approver:
                blockers.append(f"missing_human_approver:{requirement.control_id}")
                continue
            passed += 1

        if not staging_ok:
            decision = GoLiveDecision.BLOCKED_BY_STAGING
        elif blockers:
            if not_run == len(PRODUCTION_GO_LIVE_REQUIREMENTS):
                decision = GoLiveDecision.READY_FOR_HUMAN_PROMOTION
            else:
                decision = GoLiveDecision.BLOCKED
        else:
            decision = GoLiveDecision.PASS

        return FinalProductionCertificate.build(
            decision=decision,
            blockers=tuple(blockers),
            warnings=tuple(warnings),
            controls_total=len(PRODUCTION_GO_LIVE_REQUIREMENTS),
            controls_passed=passed,
            controls_not_run=not_run,
            staging_passed=staging_ok,
            metadata={
                "release_stage": "production",
                "kind": "final-production-operational-acceptance",
                "environment": "production",
                "staging_fingerprint": staging_fp,
            },
        )
