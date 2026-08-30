from __future__ import annotations
import asyncio,importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("fanout_validator",ROOT/"scripts/validate_parallel_diagnostics.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);F=V.module();S=__import__("deskpilot_ai.specialist_subgraphs",fromlist=["x"])
def item(eid,source,digest):return {"evidence_id":eid,"tenant_id":"tenant-1","incident_id":"incident-1","source":source,"kind":"health","observed_at":"2026-08-26T00:00:00Z","summary":"safe","content_included":False,"digest":digest}
def output(domain,evidence,status="complete"):return S.SpecialistOutput(domain,status,tuple(evidence),(f"{domain}-cause",),(),"safe","a"*64)
class ParallelDiagnosticsTests(unittest.IsolatedAsyncioTestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 async def test_parallel_results_are_deterministic(self):
  async def runner(domain):await asyncio.sleep(0);return output(domain,[item(f"ev-{domain}",domain,domain)])
  result=await F.fanout_diagnostics(("windows_network","outlook"),runner,tenant_id="tenant-1",incident_id="incident-1");self.assertEqual(tuple(x.domain for x in result.branches),("outlook","windows_network"));self.assertEqual(result.status,"complete");self.assertEqual(result.next_phase,"evidence_fusion")
 async def test_duplicate_digest_is_suppressed(self):
  async def runner(domain):return output(domain,[item(f"ev-{domain}","shared","same")])
  result=await F.fanout_diagnostics(("printer","windows_network"),runner,tenant_id="tenant-1",incident_id="incident-1");self.assertEqual(len(result.evidence),1)
 async def test_contradictions_are_preserved(self):
  async def runner(domain):return output(domain,[item(f"ev-{domain}","reachability",domain)])
  result=await F.fanout_diagnostics(("printer","windows_network"),runner,tenant_id="tenant-1",incident_id="incident-1");self.assertEqual(len(result.evidence),2);self.assertEqual(result.status,"contradictory");self.assertEqual(result.contradiction_keys,("reachability:health",))
 async def test_timeout_keeps_successful_partial_result(self):
  async def runner(domain):
   if domain=="windows_network":await asyncio.sleep(.03)
   return output(domain,[item(f"ev-{domain}",domain,domain)])
  result=await F.fanout_diagnostics(("printer","windows_network"),runner,tenant_id="tenant-1",incident_id="incident-1",timeout_seconds=.01);self.assertEqual(result.status,"partial");self.assertEqual(len(result.evidence),1)
 async def test_all_failed_escalates_with_safe_errors(self):
  async def runner(domain):raise RuntimeError("secret internal error")
  result=await F.fanout_diagnostics(("outlook","windows_network"),runner,tenant_id="tenant-1",incident_id="incident-1");self.assertEqual(result.next_phase,"escalated");self.assertTrue(all(x.safe_error=="branch_failed" for x in result.branches))
 async def test_invalid_branch_set_fails_closed(self):
  async def runner(domain):return output(domain,[])
  with self.assertRaises(ValueError):await F.fanout_diagnostics(("printer","printer"),runner,tenant_id="tenant-1",incident_id="incident-1")
if __name__=="__main__":unittest.main()
