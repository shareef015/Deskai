from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("evidence_fusion_validator",ROOT/"scripts/validate_evidence_fusion.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);F=V.module()
def ev(eid,source,key,value,reliability=.9,tenant="tenant-1",incident="incident-1",source_id=None):return F.Evidence(eid,tenant,incident,source,source_id or f"{source}-1",key,value,reliability,30)
class EvidenceFusionTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_cross_scope_rejected(self):
  with self.assertRaises(F.EvidenceFusionError):F.fuse_evidence("tenant-1","incident-1",(ev("e1","telemetry","dns","fail",tenant="tenant-2"),),(F.Candidate("dns",("e1",)),))
 def test_duplicate_evidence_rejected(self):
  with self.assertRaises(F.EvidenceFusionError):F.fuse_evidence("tenant-1","incident-1",(ev("e1","telemetry","dns","fail"),ev("e1","specialist","service","up")),(F.Candidate("dns",("e1",)),))
 def test_rag_alone_is_insufficient(self):
  result=F.fuse_evidence("tenant-1","incident-1",(ev("r1","rag","guidance","dns"),),(F.Candidate("dns_failure",("r1",)),));self.assertEqual(result.decision,"insufficient_evidence")
 def test_two_independent_sources_select_grounded_cause(self):
  evidence=(ev("t1","telemetry","dns_lookup","timeout",1),ev("s1","specialist","resolver","failed",.95))
  result=F.fuse_evidence("tenant-1","incident-1",evidence,(F.Candidate("dns_failure",("t1","s1")),));self.assertEqual(result.selected_root_cause,"dns_failure")
 def test_material_observation_contradiction_preserved(self):
  evidence=(ev("t1","telemetry","vpn_state","connected"),ev("s1","specialist","vpn_state","disconnected"))
  result=F.fuse_evidence("tenant-1","incident-1",evidence,(F.Candidate("vpn_failure",("s1",),("t1",)),));self.assertEqual(result.decision,"contradictory_evidence");self.assertIn("vpn_state",result.contradiction_keys)
 def test_unknown_candidate_evidence_rejected(self):
  with self.assertRaises(F.EvidenceFusionError):F.fuse_evidence("tenant-1","incident-1",(ev("e1","telemetry","dns","fail"),),(F.Candidate("dns",("missing",)),))
 def test_tie_is_not_silently_broken(self):
  evidence=(ev("t1","telemetry","a","x"),ev("s1","specialist","b","x"),ev("t2","telemetry","c","x",source_id="telemetry-2"),ev("s2","specialist","d","x",source_id="specialist-2"))
  result=F.fuse_evidence("tenant-1","incident-1",evidence,(F.Candidate("cause_a",("t1","s1")),F.Candidate("cause_b",("t2","s2"))));self.assertEqual(result.decision,"contradictory_evidence")
 def test_handoff_only_advances_grounded_result(self):
  evidence=(ev("t1","telemetry","dns","fail"),ev("s1","specialist","resolver","fail"));result=F.fuse_evidence("tenant-1","incident-1",evidence,(F.Candidate("dns_failure",("t1","s1")),));self.assertEqual(F.supervisor_handoff(result)["phase"],"remediation_planning")
if __name__=="__main__":unittest.main()
