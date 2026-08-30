from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from deskpilot_staging.certification import ConnectedStagingGate
from deskpilot_staging.dr import RecoveryObjective, RecoveryObservation, assess_recovery
from deskpilot_staging.evidence import load_evidence, write_evidence
from deskpilot_staging.models import EvidenceItem, EvidenceStatus, ReleaseDecision
from deskpilot_staging.requirements import CONNECTED_STAGING_REQUIREMENTS
from deskpilot_staging.rollout import RolloutObservation, certify_rollout


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def real_pass(control_id: str) -> EvidenceItem:
    return EvidenceItem(
        control_id=control_id,
        status=EvidenceStatus.PASS,
        source=f"staging/{control_id}/evidence.json",
        observed_at="2026-08-27T14:00:00Z",
        fingerprint=(control_id.encode().hex() + "0" * 64)[:64],
        environment="staging",
    )


class ConnectedStagingTests(unittest.TestCase):
    def test_all_required_controls_have_unique_ids(self) -> None:
        ids = [r.control_id for r in CONNECTED_STAGING_REQUIREMENTS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 20)

    def test_empty_evidence_is_ready_not_pass(self) -> None:
        cert = ConnectedStagingGate().certify(project_root=PROJECT_ROOT, evidence=())
        self.assertEqual(cert.decision, ReleaseDecision.READY_FOR_CONNECTED_STAGING)
        self.assertFalse(cert.passed)
        self.assertEqual(cert.controls_passed, 0)

    def test_all_real_evidence_can_pass(self) -> None:
        evidence = tuple(real_pass(r.control_id) for r in CONNECTED_STAGING_REQUIREMENTS)
        cert = ConnectedStagingGate().certify(project_root=PROJECT_ROOT, evidence=evidence)
        self.assertEqual(cert.decision, ReleaseDecision.PASS)
        self.assertTrue(cert.passed)
        self.assertEqual(cert.controls_passed, cert.controls_total)

    def test_synthetic_evidence_cannot_pass_real_control(self) -> None:
        evidence = [real_pass(r.control_id) for r in CONNECTED_STAGING_REQUIREMENTS]
        evidence[0] = replace(evidence[0], source="synthetic")
        cert = ConnectedStagingGate().certify(project_root=PROJECT_ROOT, evidence=tuple(evidence))
        self.assertFalse(cert.passed)
        self.assertIn(f"non_real_evidence:{evidence[0].control_id}", cert.blockers)

    def test_wrong_environment_is_blocked(self) -> None:
        evidence = [real_pass(r.control_id) for r in CONNECTED_STAGING_REQUIREMENTS]
        evidence[1] = replace(evidence[1], environment="dev")
        cert = ConnectedStagingGate().certify(project_root=PROJECT_ROOT, evidence=tuple(evidence))
        self.assertIn(f"wrong_environment:{evidence[1].control_id}", cert.blockers)

    def test_failed_control_blocks_candidate(self) -> None:
        evidence = [real_pass(r.control_id) for r in CONNECTED_STAGING_REQUIREMENTS]
        evidence[2] = replace(evidence[2], status=EvidenceStatus.FAIL)
        cert = ConnectedStagingGate().certify(project_root=PROJECT_ROOT, evidence=tuple(evidence))
        self.assertIn(f"failed:{evidence[2].control_id}", cert.blockers)

    def test_unknown_evidence_is_warning(self) -> None:
        evidence = tuple(real_pass(r.control_id) for r in CONNECTED_STAGING_REQUIREMENTS) + (real_pass("unknown_control"),)
        cert = ConnectedStagingGate().certify(project_root=PROJECT_ROOT, evidence=evidence)
        self.assertTrue(cert.passed)
        self.assertIn("unknown_evidence:unknown_control", cert.warnings)

    def test_evidence_round_trip(self) -> None:
        evidence = (real_pass("oidc_real_login"),)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.json"
            write_evidence(path, evidence)
            self.assertEqual(load_evidence(path), evidence)

    def test_recovery_objectives_pass(self) -> None:
        result = assess_recovery(
            RecoveryObjective("postgres", rpo_seconds=300, rto_seconds=1800),
            RecoveryObservation(data_loss_seconds=120, recovery_seconds=900, integrity_verified=True),
        )
        self.assertTrue(result.passed)

    def test_recovery_objectives_fail_closed(self) -> None:
        result = assess_recovery(
            RecoveryObjective("postgres", rpo_seconds=60, rto_seconds=300),
            RecoveryObservation(data_loss_seconds=120, recovery_seconds=400, integrity_verified=False),
        )
        self.assertFalse(result.passed)
        self.assertEqual(set(result.failures), {"rpo_exceeded", "rto_exceeded", "restore_integrity_not_verified"})

    def test_rollout_passes_healthy_observation(self) -> None:
        passed, failures = certify_rollout(RolloutObservation(3, 3, 1, 0.002, 700))
        self.assertTrue(passed)
        self.assertEqual(failures, ())

    def test_rollout_blocks_degraded_release(self) -> None:
        passed, failures = certify_rollout(RolloutObservation(2, 3, 2, 0.05, 2500))
        self.assertFalse(passed)
        self.assertIn("replicas_not_ready", failures)
        self.assertIn("too_many_unavailable", failures)
        self.assertIn("error_rate", failures)
        self.assertIn("latency", failures)


if __name__ == "__main__":
    unittest.main()
