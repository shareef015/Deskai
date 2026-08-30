from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("device_validator",ROOT/"scripts/validate_device_resolution.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);D=V.module()
def rel(device="WIN11-03",kind="primary",tenant="tenant-1",employee="employee-1",active=True,registered=True,os="windows_11",recent=True):return D.DeviceRelationship(tenant,employee,device,device,os,kind,f"rel-{device}",active,registered,recent)
class DeviceResolutionTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_reported_registered_device_is_proposed_for_confirmation(self):
  result=D.resolve_devices(tenant_id="tenant-1",employee_id="employee-1",relationships=(rel(),),reported_device_id="WIN11-03");self.assertEqual(result.outcome,"pending_confirmation");self.assertIsNotNone(result.confirmation_token)
 def test_confirmation_is_required_before_consent_phase(self):
  pending=D.resolve_devices(tenant_id="tenant-1",employee_id="employee-1",relationships=(rel(),),reported_device_id="WIN11-03");self.assertEqual(D.resolution_state_update(pending)["phase"],"clarification");confirmed=D.confirm_device(pending,tenant_id="tenant-1",employee_id="employee-1",device_id="WIN11-03",confirmation_token=pending.confirmation_token,decision="confirmed");self.assertEqual(D.resolution_state_update(confirmed)["phase"],"consent")
 def test_cross_tenant_result_is_rejected(self):
  with self.assertRaises(D.DeviceResolutionError):D.resolve_devices(tenant_id="tenant-1",employee_id="employee-1",relationships=(rel(tenant="tenant-2"),),reported_device_id=None)
 def test_inactive_non_windows_and_unregistered_are_filtered(self):
  records=(rel(active=False),rel(device="LINUX",os="linux"),rel(device="OLD",registered=False));self.assertEqual(D.resolve_devices(tenant_id="tenant-1",employee_id="employee-1",relationships=records,reported_device_id=None).outcome,"not_found")
 def test_close_candidates_are_ambiguous_and_disclosure_is_bounded(self):
  records=tuple(rel(device=f"WIN11-0{x}",kind="assigned",recent=False) for x in range(1,6));result=D.resolve_devices(tenant_id="tenant-1",employee_id="employee-1",relationships=records,reported_device_id=None);self.assertEqual(result.outcome,"ambiguous");self.assertEqual(len(result.candidates),3)
 def test_confirmation_token_is_scope_bound(self):
  pending=D.resolve_devices(tenant_id="tenant-1",employee_id="employee-1",relationships=(rel(),),reported_device_id="WIN11-03")
  with self.assertRaises(D.DeviceResolutionError):D.confirm_device(pending,tenant_id="tenant-2",employee_id="employee-1",device_id="WIN11-03",confirmation_token=pending.confirmation_token,decision="confirmed")
 def test_decline_does_not_select_device(self):
  pending=D.resolve_devices(tenant_id="tenant-1",employee_id="employee-1",relationships=(rel(),),reported_device_id="WIN11-03");declined=D.confirm_device(pending,tenant_id="tenant-1",employee_id="employee-1",device_id="WIN11-03",confirmation_token=pending.confirmation_token,decision="declined");self.assertIsNone(declined.selected_device_id);self.assertEqual(D.resolution_state_update(declined)["phase"],"clarification")
if __name__=="__main__":unittest.main()
