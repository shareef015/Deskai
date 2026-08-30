from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deskpilot_llmops.alerts import AlertEngine, AlertRule
from deskpilot_llmops.costs import CostLedger, ModelPriceProfile, UsageRecord
from deskpilot_llmops.drift import DriftDetector
from deskpilot_llmops.evaluation import EvaluationResult, QualityEvaluator
from deskpilot_llmops.gates import QualityThresholds, ReleaseGate
from deskpilot_llmops.golden import GoldenDataset


class EvaluationTests(unittest.TestCase):
    def test_golden_dataset_loads_and_has_both_domains(self) -> None:
        path = Path(__file__).resolve().parents[1] / "evals" / "golden" / "deskpilot_quality_golden.json"
        dataset = GoldenDataset.load(path)
        self.assertGreaterEqual(len(dataset.cases), 10)
        self.assertEqual({c.domain for c in dataset.cases}, {"outlook", "printer"})
        self.assertTrue(any(c.should_block_injection for c in dataset.cases))

    def test_retrieval_precision_and_recall(self) -> None:
        p, r = QualityEvaluator.retrieval(retrieved=["a", "b"], relevant=["a", "c"])
        self.assertEqual(p, 0.5)
        self.assertEqual(r, 0.5)

    def test_aggregate_scores_are_bounded(self) -> None:
        evaluator = QualityEvaluator()
        row = {name: 2.0 for name in EvaluationResult.__dataclass_fields__}
        result = evaluator.aggregate([row])
        self.assertTrue(all(value == 1.0 for value in result.as_dict().values()))

    def test_cost_ledger_calculates_token_cost(self) -> None:
        ledger = CostLedger([ModelPriceProfile("test", 1.0, 2.0)])
        cost = ledger.add(UsageRecord("test", 1_000_000, 500_000, 100, "run"))
        self.assertEqual(cost, 2.0)
        self.assertEqual(ledger.total_tokens(), 1_500_000)

    def test_unknown_model_price_fails_closed(self) -> None:
        ledger = CostLedger([])
        with self.assertRaises(KeyError):
            ledger.add(UsageRecord("unknown", 1, 1, 1, "run"))

    def test_quality_drift_detects_relative_drop(self) -> None:
        finding = DriftDetector(maximum_relative_drop=0.05).quality("groundedness", 0.98, 0.90)
        self.assertTrue(finding.degraded)

    def test_risk_drift_detects_hallucination_increase(self) -> None:
        finding = DriftDetector(maximum_absolute_increase=0.02).risk("hallucination_rate", 0.01, 0.04)
        self.assertTrue(finding.degraded)

    def test_alert_engine_fires_quality_alert(self) -> None:
        engine = AlertEngine([AlertRule("grounding-low", "groundedness", "lt", 0.95, "critical")])
        alerts = engine.evaluate({"groundedness": 0.90})
        self.assertEqual(len(alerts), 1)

    def test_release_gate_passes_good_candidate(self) -> None:
        evaluation = EvaluationResult(0.95, 0.95, 0.99, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0)
        cert = ReleaseGate().certify(evaluation, p95_latency_ms=1800, average_cost_usd=0.01)
        self.assertTrue(cert.passed)
        self.assertEqual(len(cert.fingerprint), 64)

    def test_release_gate_blocks_hallucination_regression(self) -> None:
        evaluation = EvaluationResult(0.95, 0.95, 0.99, 1.0, 1.0, 1.0, 0.05, 1.0, 1.0)
        cert = ReleaseGate().certify(evaluation, p95_latency_ms=1800, average_cost_usd=0.01)
        self.assertFalse(cert.passed)
        self.assertIn("hallucination_rate", cert.failures)

    def test_release_gate_blocks_latency_and_cost(self) -> None:
        evaluation = EvaluationResult(1, 1, 1, 1, 1, 1, 0, 1, 1)
        cert = ReleaseGate(QualityThresholds()).certify(evaluation, p95_latency_ms=6000, average_cost_usd=0.10)
        self.assertIn("p95_latency_ms", cert.failures)
        self.assertIn("average_cost_usd", cert.failures)


if __name__ == "__main__":
    unittest.main()
