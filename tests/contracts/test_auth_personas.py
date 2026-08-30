from __future__ import annotations
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("auth_validator",ROOT/"scripts/validate_auth_personas.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);A=V.module()
def claims(**changes):
 values=dict(subject="operator",tenant_id="tenant-1",roles=frozenset({"demo_operator","operations_viewer"}),issuer="https://identity.example.test",audience="deskpilot-api",auth_time=900,expires_at=2000,session_id="oidc-1");values.update(changes);return A.OIDCClaims(**values)
class AuthPersonaTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_invalid_issuer_is_denied(self):
  with self.assertRaises(A.AuthDenied):A.AuthStore().create_live_session(claims(issuer="https://evil.test"),now=1000)
 def test_expired_session_is_denied(self):
  store=A.AuthStore();session=store.create_live_session(claims(),now=1000)
  with self.assertRaises(A.AuthDenied):store.authorize(session.session_id,now=2000)
 def test_tenant_mismatch_is_denied(self):
  store=A.AuthStore();session=store.create_live_session(claims(),now=1000)
  with self.assertRaises(A.AuthDenied):store.authorize(session.session_id,tenant_id="tenant-2",now=1001)
 def test_demo_session_is_disabled_in_production(self):
  with self.assertRaises(A.AuthDenied):A.AuthStore(production=True).create_demo_session(claims(),"employee",now=1000)
 def test_demo_requires_operator_role(self):
  with self.assertRaises(A.AuthDenied):A.AuthStore().create_demo_session(claims(roles=frozenset({"employee"})),"employee",now=1000)
 def test_live_session_cannot_switch_persona(self):
  store=A.AuthStore();session=store.create_live_session(claims(),now=1000)
  with self.assertRaises(A.AuthDenied):store.switch_demo_persona(session.session_id,"employee",now=1001)
 def test_logout_revokes_session(self):
  store=A.AuthStore();session=store.create_live_session(claims(),now=1000);store.logout(session.session_id,now=1001)
  with self.assertRaises(A.AuthDenied):store.authorize(session.session_id,now=1002)
 def test_navigation_is_role_scoped_and_audit_is_hashed(self):
  store=A.AuthStore();session=store.create_demo_session(claims(),"employee",now=1000);switched=store.switch_demo_persona(session.session_id,"operations",now=1001);self.assertIn("operations",store.navigation(switched.session_id,now=1002));self.assertNotIn("operator",store.audit[0].actor_sha256);self.assertEqual(len(store.audit[-1].event_sha256),64)
if __name__=="__main__":unittest.main()
