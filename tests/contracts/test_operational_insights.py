from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("insights_validator",ROOT/"scripts/validate_operational_insights.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);O=V.module();CTX=O.InsightContext("tenant-1","synthetic",frozenset({"operations_viewer"}),"2026-08-20T00:00:00Z","2026-08-27T00:00:00Z");SERIES=(O.MetricSeries("rag_quality","percent",(O.MetricPoint("2026-08-21T00:00:00Z",94),)),)
class OperationalInsightsTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_valid_snapshot_is_fingerprinted(self):self.assertEqual(len(O.build_snapshot(CTX,SERIES,"2026-08-27T01:00:00Z").fingerprint),64)
 def test_wrong_role_is_denied(self):
  with self.assertRaises(O.InsightDenied):O.build_snapshot(O.InsightContext("t","live",frozenset({"employee"}),CTX.window_start,CTX.window_end),SERIES,"2026-08-27T01:00:00Z")
 def test_window_is_bounded(self):
  with self.assertRaises(O.InsightDenied):O.build_snapshot(O.InsightContext("t","live",frozenset({"operations_viewer"}),"2026-01-01T00:00:00Z","2026-08-27T00:00:00Z"),SERIES,"2026-08-27T01:00:00Z")
 def test_wrong_unit_is_denied(self):
  with self.assertRaises(O.InsightDenied):O.build_snapshot(CTX,(O.MetricSeries("rag_quality","count",SERIES[0].points),),"2026-08-27T01:00:00Z")
 def test_percent_over_100_is_denied(self):
  with self.assertRaises(O.InsightDenied):O.build_snapshot(CTX,(O.MetricSeries("rag_quality","percent",(O.MetricPoint("2026-08-21T00:00:00Z",101),)),),"2026-08-27T01:00:00Z")
 def test_out_of_window_point_is_denied(self):
  with self.assertRaises(O.InsightDenied):O.build_snapshot(CTX,(O.MetricSeries("agent_latency","milliseconds",(O.MetricPoint("2026-08-19T00:00:00Z",100),)),),"2026-08-27T01:00:00Z")
 def test_duplicate_metric_is_denied(self):
  with self.assertRaises(O.InsightDenied):O.build_snapshot(CTX,SERIES+SERIES,"2026-08-27T01:00:00Z")
 def test_point_order_does_not_change_fingerprint(self):
  points=(O.MetricPoint("2026-08-21T00:00:00Z",94),O.MetricPoint("2026-08-22T00:00:00Z",95));a=(O.MetricSeries("rag_quality","percent",points),);b=(O.MetricSeries("rag_quality","percent",tuple(reversed(points))),);self.assertEqual(O.build_snapshot(CTX,a,"2026-08-27T01:00:00Z").fingerprint,O.build_snapshot(CTX,b,"2026-08-27T01:00:00Z").fingerprint)
if __name__=="__main__":unittest.main()
