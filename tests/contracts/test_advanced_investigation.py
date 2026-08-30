from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("investigation_validator",ROOT/"scripts/validate_advanced_investigation.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);I=V.module();CTX=I.InvestigationContext("tenant-1","inc-1","engineer",frozenset({"service_desk_engineer"}),True,"synthetic");NODES=(I.EvidenceNode("incident","incident","Outlook disconnected",("ev-1",)),I.EvidenceNode("dns","observation","DNS healthy",("ev-2",)));EDGES=(I.EvidenceEdge("incident","dns","checked_by",("ev-3",)),)
class AdvancedInvestigationTests(unittest.TestCase):
 def test_policy_and_route_ownership_valid(self):self.assertEqual(V.validate(),[])
 def test_authorized_grounded_view_is_created(self):self.assertEqual(I.build_view(CTX,NODES,EDGES,("ret-1",),("trace-1",),("Outlook specialist complete",)).incident_id,"inc-1")
 def test_unauthorized_role_is_denied(self):
  with self.assertRaises(I.InvestigationDenied):I.build_view(I.InvestigationContext("t","i","a",frozenset({"employee"}),True,"live"),NODES,EDGES,(),(),())
 def test_missing_consent_is_denied(self):
  with self.assertRaises(I.InvestigationDenied):I.build_view(I.InvestigationContext("t","i","a",frozenset({"service_desk_engineer"}),False,"live"),NODES,EDGES,(),(),())
 def test_ungrounded_node_is_denied(self):
  with self.assertRaises(I.InvestigationDenied):I.build_view(CTX,(I.EvidenceNode("x","entity","X",()),),(),(),(),())
 def test_dangling_edge_is_denied(self):
  with self.assertRaises(I.InvestigationDenied):I.build_view(CTX,NODES,(I.EvidenceEdge("incident","missing","rel",("ev",)),),(),(),())
 def test_duplicate_node_id_is_denied(self):
  with self.assertRaises(I.InvestigationDenied):I.build_view(CTX,(NODES[0],NODES[0]),(),(),(),())
 def test_graph_budget_is_enforced(self):
  with self.assertRaises(I.InvestigationDenied):I.build_view(CTX,tuple(I.EvidenceNode(str(n),"entity","x",("ev",)) for n in range(81)),(),(),(),())
 def test_view_fingerprint_is_order_independent(self):self.assertEqual(I.build_view(CTX,NODES,EDGES,("b","a"),("z","y"),("s2","s1")).provenance_sha256,I.build_view(CTX,tuple(reversed(NODES)),EDGES,("a","b"),("y","z"),("s1","s2")).provenance_sha256)
if __name__=="__main__":unittest.main()
