from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("verification_validator",ROOT/"scripts/validate_outcome_verification.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);O=V.module()
def context(**changes):
 values=dict(tenant_id="tenant-1",incident_id="incident-1",device_id="WIN11-03",domain="network",plan_id="rmp-1",plan_provenance_sha256="a"*64,execution_result_fingerprint="b"*64,execution_status="succeeded",rollback_supported=True,original_business_function="Outlook connectivity");values.update(changes);return O.VerificationContext(**values)
def check(cid="business",ctype="target_business_function",status="pass",expected="works",observed="works",**changes):
 values=dict(check_id=cid,check_type=ctype,evidence_id=f"ev-{cid}",expected_value=expected,observed_value=observed,status=status,read_only=True,bounded=True);values.update(changes);return O.CheckResult(**values)
class OutcomeVerificationTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_successful_business_check_waits_for_employee(self):self.assertEqual(O.evaluate(context=context(),targeted_checks=(check(),),regression_checks=()).outcome,"awaiting_confirmation")
 def test_failed_check_routes_to_rollback(self):self.assertEqual(O.evaluate(context=context(),targeted_checks=(check(status="fail",observed="broken"),),regression_checks=()).recovery_route,"rollback")
 def test_regression_routes_to_rollback(self):
  result=O.evaluate(context=context(),targeted_checks=(check(),),regression_checks=(check("reg","dns_resolution","fail","works","fails"),));self.assertEqual(result.outcome,"regression")
 def test_unknown_or_missing_business_check_is_inconclusive(self):self.assertEqual(O.evaluate(context=context(),targeted_checks=(check("dns","dns_resolution"),),regression_checks=()).outcome,"inconclusive")
 def test_unbounded_or_mutating_check_rejected(self):
  with self.assertRaises(O.VerificationError):O.evaluate(context=context(),targeted_checks=(check(read_only=False),),regression_checks=())
 def test_success_claim_must_match_observation(self):
  with self.assertRaises(O.VerificationError):O.evaluate(context=context(),targeted_checks=(check(observed="broken"),),regression_checks=())
 def test_employee_confirmation_must_match_scope_and_provenance(self):
  result=O.evaluate(context=context(),targeted_checks=(check(),),regression_checks=());confirmation=O.EmployeeConfirmation("employee-1","tenant-1","incident-1","WIN11-03",True,True,"confirmed","c"*64)
  with self.assertRaises(O.VerificationError):O.validate_employee_confirmation(context(),result,confirmation)
 def test_only_authenticated_employee_confirmation_resolves(self):
  result=O.evaluate(context=context(),targeted_checks=(check(),),regression_checks=());confirmation=O.EmployeeConfirmation("employee-1","tenant-1","incident-1","WIN11-03",True,True,"confirmed",result.provenance_sha256);self.assertEqual(O.validate_employee_confirmation(context(),result,confirmation)["phase"],"resolved")
if __name__=="__main__":unittest.main()
