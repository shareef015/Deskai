from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from deskpilot_release.artifact import ArtifactPromotion, certify_artifact_promotion
from deskpilot_release.canary import CanaryObservation, certify_canary
from deskpilot_release.certification import FinalProductionGate
from deskpilot_release.evidence import load_production_evidence, write_production_evidence
from deskpilot_release.models import GoLiveDecision, ProductionEvidenceItem, ProductionEvidenceStatus
from deskpilot_release.prerequisites import staging_connected_pass
from deskpilot_release.requirements import PRODUCTION_GO_LIVE_REQUIREMENTS


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def real_prod_pass(control_id: str, *, approver: str | None = "release-authority") -> ProductionEvidenceItem:
    return ProductionEvidenceItem(
        control_id=control_id,
        status=ProductionEvidenceStatus.PASS,
        source=f"production/{control_id}/evidence.json",
        observed_at="2026-08-27T15:00:00Z",
        fingerprint=(control_id.encode().hex() + "0" * 64)[:64],
        approver=approver,
        environment="production",
    )


def fake_project_with_staging(*, passed: bool) -> Path:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    report = root / "backend" / "staging" / "reports" / "CONNECTED_STAGING_CERTIFICATION.json"
    report.parent.mkdir(parents=True)
    report.write_text(
        json.dumps(
            {
                "certificate": {
                    "passed": passed,
                    "decision": "pass" if passed else "ready_for_connected_staging",
                    "fingerprint": "a" * 64,
                }
            }
        ),
        encoding="utf-8",
    )
    root._tmp_ref = tmp  # type: ignore[attr-defined]
    return root


class ProductionGoLiveTests(unittest.TestCase):
    def test_current_project_is_blocked_by_staging(self) -> None:
        self.assertFalse(staging_connected_pass(PROJECT_ROOT))
        cert = FinalProductionGate().certify(project_root=PROJECT_ROOT, evidence=())
        self.assertEqual(cert.decision, GoLiveDecision.BLOCKED_BY_STAGING)
        self.assertFalse(cert.passed)
        self.assertIn("staging_connected_certificate_not_passing", cert.blockers)

    def test_staging_pass_with_no_production_evidence_is_ready_for_human_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / "backend" / "staging" / "reports" / "CONNECTED_STAGING_CERTIFICATION.json"
            report.parent.mkdir(parents=True)
            report.write_text(json.dumps({"certificate": {"passed": True, "decision": "pass", "fingerprint": "a" * 64}}))
            cert = FinalProductionGate().certify(project_root=root, evidence=())
            self.assertEqual(cert.decision, GoLiveDecision.READY_FOR_HUMAN_PROMOTION)
            self.assertFalse(cert.passed)

    def test_all_real_approved_production_evidence_can_pass_after_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / "backend" / "staging" / "reports" / "CONNECTED_STAGING_CERTIFICATION.json"
            report.parent.mkdir(parents=True)
            report.write_text(json.dumps({"certificate": {"passed": True, "decision": "pass", "fingerprint": "a" * 64}}))
            evidence = tuple(real_prod_pass(r.control_id) for r in PRODUCTION_GO_LIVE_REQUIREMENTS)
            cert = FinalProductionGate().certify(project_root=root, evidence=evidence)
            self.assertEqual(cert.decision, GoLiveDecision.PASS)
            self.assertTrue(cert.passed)
            self.assertEqual(cert.controls_passed, cert.controls_total)

    def test_human_approval_cannot_be_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / "backend" / "staging" / "reports" / "CONNECTED_STAGING_CERTIFICATION.json"
            report.parent.mkdir(parents=True)
            report.write_text(json.dumps({"certificate": {"passed": True, "decision": "pass", "fingerprint": "a" * 64}}))
            evidence = [real_prod_pass(r.control_id) for r in PRODUCTION_GO_LIVE_REQUIREMENTS]
            index = next(i for i, r in enumerate(PRODUCTION_GO_LIVE_REQUIREMENTS) if r.control_id == "human_go_no_go")
            evidence[index] = replace(evidence[index], approver=None)
            cert = FinalProductionGate().certify(project_root=root, evidence=tuple(evidence))
            self.assertIn("missing_human_approver:human_go_no_go", cert.blockers)

    def test_synthetic_production_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / "backend" / "staging" / "reports" / "CONNECTED_STAGING_CERTIFICATION.json"
            report.parent.mkdir(parents=True)
            report.write_text(json.dumps({"certificate": {"passed": True, "decision": "pass", "fingerprint": "a" * 64}}))
            evidence = [real_prod_pass(r.control_id) for r in PRODUCTION_GO_LIVE_REQUIREMENTS]
            evidence[0] = replace(evidence[0], source="synthetic")
            cert = FinalProductionGate().certify(project_root=root, evidence=tuple(evidence))
            self.assertIn("non_real_evidence:human_go_no_go", cert.blockers)

    def test_staging_evidence_cannot_satisfy_production_control(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = root / "backend" / "staging" / "reports" / "CONNECTED_STAGING_CERTIFICATION.json"
            report.parent.mkdir(parents=True)
            report.write_text(json.dumps({"certificate": {"passed": True, "decision": "pass", "fingerprint": "a" * 64}}))
            evidence = [real_prod_pass(r.control_id) for r in PRODUCTION_GO_LIVE_REQUIREMENTS]
            evidence[1] = replace(evidence[1], environment="staging")
            cert = FinalProductionGate().certify(project_root=root, evidence=tuple(evidence))
            self.assertIn(f"non_real_evidence:{evidence[1].control_id}", cert.blockers)

    def test_production_evidence_round_trip(self) -> None:
        evidence = (real_prod_pass("human_go_no_go"),)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "production-evidence.json"
            write_production_evidence(path, evidence)
            self.assertEqual(load_production_evidence(path), evidence)

    def test_artifact_promotion_requires_identical_digest_and_attestation(self) -> None:
        digest = "sha256:" + "a" * 64
        passed, failures = certify_artifact_promotion(ArtifactPromotion(digest, digest, True, True, False))
        self.assertTrue(passed)
        self.assertEqual(failures, ())

    def test_artifact_rebuild_or_digest_change_is_blocked(self) -> None:
        passed, failures = certify_artifact_promotion(
            ArtifactPromotion("sha256:" + "a" * 64, "sha256:" + "b" * 64, True, True, True)
        )
        self.assertFalse(passed)
        self.assertIn("digest_changed", failures)
        self.assertIn("artifact_rebuilt_after_staging", failures)

    def test_canary_passes_healthy_release(self) -> None:
        passed, failures = certify_canary(CanaryObservation(0.002, 700, 0.55, 1.0, 0.99))
        self.assertTrue(passed)
        self.assertEqual(failures, ())

    def test_canary_blocks_quality_and_reliability_regression(self) -> None:
        passed, failures = certify_canary(CanaryObservation(0.05, 2200, 0.95, 0.8, 0.7))
        self.assertFalse(passed)
        self.assertEqual(set(failures), {"error_rate", "latency", "saturation", "golden_regression", "groundedness_regression"})

    def test_requirements_are_unique_and_include_final_acceptance(self) -> None:
        ids = [item.control_id for item in PRODUCTION_GO_LIVE_REQUIREMENTS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("final_operational_acceptance", ids)
        self.assertIn("recruiter_portfolio_package", ids)
        self.assertGreaterEqual(len(ids), 15)


if __name__ == "__main__":
    unittest.main()
