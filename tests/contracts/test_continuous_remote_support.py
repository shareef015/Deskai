from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("remote_validator",ROOT/"scripts/validate_continuous_remote_support.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);R=V.module()
def request(**changes):
 values=dict(request_id="req-1",tenant_id="tenant-1",incident_id="inc-1",employee_id="employee-1",device_id="WIN11-03",support_actor_id="engineer-1",capabilities=frozenset({"view_screen","control_pointer","use_support_ui"}),expires_at=1100,purpose="Diagnose Outlook disconnected issue");values.update(changes);return R.RemoteAccessRequest(**values)
class ContinuousRemoteSupportTests(unittest.TestCase):
 def test_policy_and_ui_flow_valid(self):self.assertEqual(V.validate(),[])
 def test_employee_allow_creates_active_session(self):
  store=R.RemoteSupportStore();store.request(request(),now=1000);self.assertEqual(store.decide(R.EmployeeDecision("req-1","employee-1","allow",1001),now=1001).status,"active")
 def test_decline_never_creates_active_access(self):
  store=R.RemoteSupportStore();store.request(request(),now=1000);self.assertEqual(store.decide(R.EmployeeDecision("req-1","employee-1","decline",1001),now=1001).status,"declined")
 def test_request_is_short_lived(self):
  with self.assertRaises(R.RemoteSupportDenied):R.RemoteSupportStore().request(request(expires_at=2000),now=1000)
 def test_wrong_employee_cannot_decide(self):
  store=R.RemoteSupportStore();store.request(request(),now=1000)
  with self.assertRaises(R.RemoteSupportDenied):store.decide(R.EmployeeDecision("req-1","other","allow",1001),now=1001)
 def test_ui_authorization_is_scope_bound(self):
  store=R.RemoteSupportStore();store.request(request(),now=1000);session=store.decide(R.EmployeeDecision("req-1","employee-1","allow",1001),now=1001)
  with self.assertRaises(R.RemoteSupportDenied):store.authorize_ui(session.session_id,tenant_id="tenant-1",incident_id="inc-1",device_id="OTHER",capability="use_support_ui",now=1002)
 def test_unrequested_capability_is_denied(self):
  store=R.RemoteSupportStore();store.request(request(capabilities=frozenset({"view_screen"})),now=1000);session=store.decide(R.EmployeeDecision("req-1","employee-1","allow",1001),now=1001)
  with self.assertRaises(R.RemoteSupportDenied):store.authorize_ui(session.session_id,tenant_id="tenant-1",incident_id="inc-1",device_id="WIN11-03",capability="control_pointer",now=1002)
 def test_employee_revocation_stops_authorization(self):
  store=R.RemoteSupportStore();store.request(request(),now=1000);session=store.decide(R.EmployeeDecision("req-1","employee-1","allow",1001),now=1001);store.revoke(session.session_id,"employee-1")
  with self.assertRaises(R.RemoteSupportDenied):store.authorize_ui(session.session_id,tenant_id="tenant-1",incident_id="inc-1",device_id="WIN11-03",capability="view_screen",now=1002)
 def test_support_end_is_terminal(self):
  store=R.RemoteSupportStore();store.request(request(),now=1000);session=store.decide(R.EmployeeDecision("req-1","employee-1","allow",1001),now=1001);store.end(session.session_id,"engineer-1");self.assertEqual(session.status,"ended")
if __name__=="__main__":unittest.main()
