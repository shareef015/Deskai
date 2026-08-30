from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("shell_validator",ROOT/"scripts/validate_application_shell.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);S=V.module()
def context(**changes):
 values=dict(tenant_id="tenant-1",tenant_label="Northwind",roles=frozenset({"service_desk_engineer"}),mode="live",authenticated=True);values.update(changes);return S.ShellContext(**values)
class ApplicationShellTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_unauthenticated_context_is_denied(self):
  with self.assertRaises(S.NavigationDenied):S.build_manifest(context(authenticated=False))
 def test_tenant_context_is_required(self):
  with self.assertRaises(S.NavigationDenied):S.build_manifest(context(tenant_id=""))
 def test_employee_navigation_is_minimal(self):self.assertEqual([i.key for _,items in S.build_manifest(context(roles=frozenset({"employee"}))).groups for i in items],["incidents","conversation"])
 def test_approver_cannot_open_operations(self):
  with self.assertRaises(S.NavigationDenied):S.authorize_path(context(roles=frozenset({"remediation_approver"})),"/operations")
 def test_demo_destination_is_synthetic_only(self):
  with self.assertRaises(S.NavigationDenied):S.authorize_path(context(roles=frozenset({"demo_operator"}),mode="live"),"/guided-demo")
 def test_demo_operator_sees_demo_in_synthetic_mode(self):self.assertEqual(S.authorize_path(context(roles=frozenset({"demo_operator"}),mode="synthetic"),"/guided-demo").key,"demo")
 def test_groups_have_stable_policy_order(self):self.assertEqual([g for g,_ in S.build_manifest(context()).groups],["Support","Investigation","Resolution"])
 def test_manifest_fingerprint_is_deterministic(self):self.assertEqual(S.build_manifest(context()).manifest_sha256,S.build_manifest(context()).manifest_sha256)
if __name__=="__main__":unittest.main()
