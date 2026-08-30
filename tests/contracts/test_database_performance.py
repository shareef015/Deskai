from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("db_performance", ROOT / "scripts/validate_database_performance.py")
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
POLICY = json.loads((ROOT / "contracts/database-performance-policy.json").read_text())


class DatabasePerformanceTests(unittest.TestCase):
    def test_performance_contract_is_valid(self):
        self.assertEqual(VALIDATOR.validate(), [])

    def test_query_budget_fits_api_budget(self):
        targets = POLICY["targets"]
        self.assertLess(targets["interactive_query_p95_ms"], targets["api_total_p95_ms"])

    def test_keyset_pagination_is_required(self):
        self.assertEqual(POLICY["pagination"]["strategy"], "keyset")
        self.assertTrue(POLICY["pagination"]["offset_pagination_for_large_sets_prohibited"])

    def test_plan_analysis_uses_representative_data(self):
        self.assertTrue(POLICY["plan_gates"]["explain_analyze_on_synthetic_data_required"])

    def test_slow_query_observability_is_required(self):
        self.assertTrue(POLICY["operations"]["pg_stat_statements_required"])
        self.assertEqual(POLICY["targets"]["slow_query_threshold_ms"], 500)
