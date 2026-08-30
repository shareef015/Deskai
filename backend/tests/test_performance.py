from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from deskpilot_performance.autoscaling import desired_replicas
from deskpilot_performance.cache import evaluate_cache
from deskpilot_performance.certification import PerformanceGate
from deskpilot_performance.degradation import DegradationMode, decide_degradation
from deskpilot_performance.fairness import enforce_tenant_share, jain_fairness_index
from deskpilot_performance.models import ResourceSnapshot
from deskpilot_performance.queueing import assess_queue
from deskpilot_performance.simulation import DEFAULT_ENVELOPE, DEFAULT_STAGE_BUDGETS, synthetic_baseline, synthetic_regression
from deskpilot_performance.soak import assess_soak
from deskpilot_performance.stats import percentile, summarize_stage


class PerformancePerformanceTests(unittest.TestCase):
    def test_percentile_nearest_rank_is_deterministic(self) -> None:
        self.assertEqual(percentile([1, 2, 3, 4, 5], 95), 5)

    def test_stage_summary_computes_error_rate(self) -> None:
        summary = summarize_stage("api", [10, 20, 30, 40], errors=1)
        self.assertEqual(summary.error_rate, 0.25)
        self.assertEqual(summary.max_ms, 40)

    def test_jain_fairness_is_one_for_equal_tenants(self) -> None:
        self.assertEqual(jain_fairness_index([10, 10, 10, 10]), 1.0)

    def test_jain_fairness_detects_noisy_neighbor(self) -> None:
        self.assertLess(jain_fairness_index([90, 5, 3, 2]), 0.5)

    def test_tenant_share_caps_single_tenant(self) -> None:
        allocation = enforce_tenant_share({"a": 100, "b": 10}, total_slots=100, max_share=0.5)
        self.assertLessEqual(allocation["a"], 50)
        self.assertLessEqual(sum(allocation.values()), 100)

    def test_cache_efficiency_reports_avoided_compute_and_cost(self) -> None:
        result = evaluate_cache(requests=100, hits=70, compute_ms_per_miss=200, cost_usd_per_miss=0.01)
        self.assertEqual(result.hit_ratio, 0.7)
        self.assertEqual(result.avoided_compute_ms, 14_000)
        self.assertAlmostEqual(result.avoided_cost_usd, 0.7)

    def test_stable_queue_has_bounded_drain_time(self) -> None:
        result = assess_queue(arrival_rate=8, service_rate=10, backlog=20)
        self.assertTrue(result.stable)
        self.assertEqual(result.drain_seconds, 10)

    def test_unstable_queue_is_flagged(self) -> None:
        result = assess_queue(arrival_rate=12, service_rate=10, backlog=20)
        self.assertFalse(result.stable)
        self.assertIsNone(result.drain_seconds)

    def test_autoscaler_scales_up_but_respects_growth_cap(self) -> None:
        result = desired_replicas(current_replicas=4, observed_utilization=1.2, target_utilization=0.6, minimum=2, maximum=20)
        self.assertEqual(result.desired_replicas, 8)
        self.assertEqual(result.reason, "scale_up")

    def test_autoscaler_respects_maximum(self) -> None:
        result = desired_replicas(current_replicas=10, observed_utilization=2.0, target_utilization=0.5, minimum=2, maximum=12)
        self.assertEqual(result.desired_replicas, 12)

    def test_soak_test_detects_memory_leak_slope(self) -> None:
        result = assess_soak(hours=4, memory_start_mb=500, memory_end_mb=580, connections_start=100, connections_end=101)
        self.assertFalse(result.stable)
        self.assertIn("memory_growth", result.failures)

    def test_soak_test_passes_stable_process(self) -> None:
        result = assess_soak(hours=8, memory_start_mb=500, memory_end_mb=520, connections_start=100, connections_end=102)
        self.assertTrue(result.stable)

    def test_graceful_degradation_sheds_optional_work_first(self) -> None:
        resources = ResourceSnapshot(0.82, 0.6, 0.6, 0.6, 0.7, 30)
        decision = decide_degradation(resources, queue_oldest_age_seconds=5)
        self.assertEqual(decision.mode, DegradationMode.SHED_OPTIONAL)
        self.assertTrue(decision.allow_remediation)
        self.assertFalse(decision.allow_optional_enrichment)

    def test_critical_pressure_protects_remediation_boundary(self) -> None:
        resources = ResourceSnapshot(0.99, 0.7, 0.7, 0.7, 0.7, 1000)
        decision = decide_degradation(resources, queue_oldest_age_seconds=5)
        self.assertEqual(decision.mode, DegradationMode.PROTECTIVE)
        self.assertFalse(decision.allow_remediation)

    def test_synthetic_baseline_passes_performance_gate(self) -> None:
        certificate = PerformanceGate(DEFAULT_STAGE_BUDGETS).certify(synthetic_baseline(), DEFAULT_ENVELOPE)
        self.assertTrue(certificate.passed, certificate.failures)
        self.assertEqual(len(certificate.fingerprint), 64)

    def test_synthetic_regression_is_blocked(self) -> None:
        certificate = PerformanceGate(DEFAULT_STAGE_BUDGETS).certify(synthetic_regression(), DEFAULT_ENVELOPE)
        self.assertFalse(certificate.passed)
        self.assertIn("throughput", certificate.failures)
        self.assertIn("tenant_fairness", certificate.failures)
        self.assertIn("dropped_requests", certificate.failures)
        self.assertTrue(any(item.startswith("resource:") for item in certificate.failures))


if __name__ == "__main__":
    unittest.main()

class PerformanceCapacityControlTests(unittest.TestCase):
    def test_concurrency_governor_blocks_tenant_noisy_neighbor(self) -> None:
        from deskpilot_performance.concurrency import CapacityExceeded, ConcurrencyGovernor
        governor = ConcurrencyGovernor(limits={"agent": 4}, tenant_share_max=0.5)
        first = governor.acquire(tenant_id="a", workload="agent")
        second = governor.acquire(tenant_id="a", workload="agent")
        with self.assertRaises(CapacityExceeded):
            governor.acquire(tenant_id="a", workload="agent")
        governor.release(first)
        governor.release(second)

    def test_concurrency_governor_tracks_utilization(self) -> None:
        from deskpilot_performance.concurrency import ConcurrencyGovernor
        governor = ConcurrencyGovernor(limits={"mcp": 4}, tenant_share_max=1.0)
        lease = governor.acquire(tenant_id="a", workload="mcp")
        self.assertEqual(governor.utilization("mcp"), 0.25)
        governor.release(lease)
        self.assertEqual(governor.utilization("mcp"), 0.0)

    def test_model_route_budget_filters_slow_or_expensive_models(self) -> None:
        from deskpilot_performance.model_routing import ModelPerformanceProfile, ModelRouteBudget, eligible_models
        profiles = (
            ModelPerformanceProfile("fast", 800, 100, 1.0, 2.0, 0.95),
            ModelPerformanceProfile("slow", 3000, 100, 1.0, 2.0, 0.99),
            ModelPerformanceProfile("expensive", 700, 100, 100.0, 200.0, 0.99),
        )
        budget = ModelRouteBudget(1500, 20, 0.05, 0.90, 1000, 500)
        self.assertEqual([p.model for p in eligible_models(profiles, budget)], ["fast"])

    def test_postgres_or_redis_waiters_mark_pool_saturated(self) -> None:
        from deskpilot_performance.pools import assess_pool
        result = assess_pool(active=6, maximum=10, waiting=2)
        self.assertTrue(result.saturated)

    def test_stream_fanout_preserves_twenty_percent_headroom(self) -> None:
        from deskpilot_performance.fanout import assess_fanout
        self.assertTrue(assess_fanout(active_connections=800, maximum_connections=1000).safe)
        self.assertFalse(assess_fanout(active_connections=900, maximum_connections=1000).safe)
