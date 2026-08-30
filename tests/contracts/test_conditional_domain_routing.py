from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("domain_validator",ROOT/"scripts/validate_conditional_domain_routing.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);R=V.module()
class ConditionalDomainRoutingTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_clear_winner_routes_single_specialist(self):
  route=R.select_domain_route([R.DomainScore("printer",.94,("queue",)),R.DomainScore("windows_network",.40)],clarification_rounds=0);self.assertEqual(route.next_nodes,("printer_specialist",));self.assertEqual(route.outcome,"single")
 def test_close_high_scores_route_bounded_parallel(self):
  route=R.select_domain_route([R.DomainScore("outlook",.88),R.DomainScore("windows_network",.80)],clarification_rounds=0);self.assertEqual(route.outcome,"parallel");self.assertEqual(route.domains,("outlook","windows_network"))
 def test_low_confidence_clarifies_then_escalates(self):
  candidate=[R.DomainScore("scanner",.55)];self.assertEqual(R.select_domain_route(candidate,clarification_rounds=2).outcome,"clarify");self.assertEqual(R.select_domain_route(candidate,clarification_rounds=3).outcome,"escalate")
 def test_invalid_and_duplicate_candidates_escalate(self):
  self.assertEqual(R.select_domain_route([R.DomainScore("linux",.9)],clarification_rounds=0).reason,"invalid_candidate_set");self.assertEqual(R.select_domain_route([R.DomainScore("printer",.9),R.DomainScore("printer",.8)],clarification_rounds=0).reason,"duplicate_domain_candidate")
 def test_routing_is_order_independent_and_auditable(self):
  a=R.DomainScore("outlook",.91,("send_receive",));b=R.DomainScore("printer",.2);one=R.select_domain_route([a,b],clarification_rounds=0);two=R.select_domain_route([b,a],clarification_rounds=0);self.assertEqual(one,two);self.assertEqual(len(one.provenance_sha256),64)
if __name__=="__main__":unittest.main()
