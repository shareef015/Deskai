from __future__ import annotations
import dataclasses,datetime as dt,hashlib,hmac,importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];SPEC=importlib.util.spec_from_file_location("mcp_validator",ROOT/"scripts/validate_mcp_dispatch.py");assert SPEC and SPEC.loader
V=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V);M=V.module();NOW=dt.datetime(2026,8,27,12,0,tzinfo=dt.timezone.utc);KEY=b"k"*32
A=M.EndpointAttestation("tenant-1","WIN11-03","agent-1","a"*64,"1.2.0","b"*64,"healthy","2026-08-27T11:59:00Z","c"*64);C=M.AuthorizedCapability("tenant-1","incident-1","WIN11-03","service_status","1.0.0","read_service",{"service_name":"Spooler"},"d"*64,None)
def envelope(att=A):return M.dispatch(C,att,now=NOW,ttl_seconds=120,signing_key=KEY,approved_agent_builds=frozenset({"1.2.0"}),expected_policy_fingerprint="b"*64)
def result(e,**changes):
 vals=dict(envelope_id=e.envelope_id,nonce=e.nonce,tenant_id=e.tenant_id,incident_id=e.incident_id,device_id=e.device_id,tool_id=e.tool_id,tool_version=e.tool_version,status="success",typed_fields={"state":"running"},evidence_ids=("ev-1",),content_included=False,result_sha256="e"*64)
 vals.update(changes);sig=hmac.new(KEY,json.dumps(vals,sort_keys=True,separators=(",",":"),default=list).encode(),hashlib.sha256).hexdigest();return M.MCPResult(**vals,signature_sha256=sig)
class MCPDispatchTests(unittest.TestCase):
 def test_policy_valid(self):self.assertEqual(V.validate(),[])
 def test_healthy_attested_endpoint_receives_envelope(self):self.assertEqual(envelope().endpoint_agent_id,"agent-1")
 def test_degraded_or_unapproved_build_denied(self):
  with self.assertRaises(M.MCPDenied):envelope(dataclasses.replace(A,health="degraded"))
  with self.assertRaises(M.MCPDenied):M.dispatch(C,A,now=NOW,ttl_seconds=120,signing_key=KEY,approved_agent_builds=frozenset({"2.0.0"}),expected_policy_fingerprint="b"*64)
 def test_expired_or_replayed_envelope_denied(self):
  e=envelope()
  with self.assertRaises(M.MCPDenied):M.validate_result(e,result(e),now=NOW+dt.timedelta(seconds=121),signing_key=KEY,seen_nonces=frozenset(),allowed_result_keys=frozenset({"state"}))
  with self.assertRaises(M.MCPDenied):M.validate_result(e,result(e),now=NOW,signing_key=KEY,seen_nonces=frozenset({e.nonce}),allowed_result_keys=frozenset({"state"}))
 def test_cross_device_result_denied(self):
  e=envelope()
  with self.assertRaises(M.MCPDenied):M.validate_result(e,result(e,device_id="WIN11-04"),now=NOW,signing_key=KEY,seen_nonces=frozenset(),allowed_result_keys=frozenset({"state"}))
 def test_raw_content_or_unknown_result_key_denied(self):
  e=envelope()
  with self.assertRaises(M.MCPDenied):M.validate_result(e,result(e,content_included=True),now=NOW,signing_key=KEY,seen_nonces=frozenset(),allowed_result_keys=frozenset({"state"}))
  with self.assertRaises(M.MCPDenied):M.validate_result(e,result(e,typed_fields={"raw":"x"}),now=NOW,signing_key=KEY,seen_nonces=frozenset(),allowed_result_keys=frozenset({"state"}))
 def test_tampered_envelope_denied(self):
  e=dataclasses.replace(envelope(),capability_id="other")
  with self.assertRaises(M.MCPDenied):M.validate_result(e,result(e),now=NOW,signing_key=KEY,seen_nonces=frozenset(),allowed_result_keys=frozenset({"state"}))
 def test_valid_result_preserves_lineage(self):
  e=envelope();validated=M.validate_result(e,result(e),now=NOW,signing_key=KEY,seen_nonces=frozenset(),allowed_result_keys=frozenset({"state"}));self.assertEqual(validated["mcp_dispatch_status"],"validated");self.assertEqual(len(validated["mcp_evidence_lineage_sha256"]),64)
 def test_noncompliant_agent_can_be_quarantined(self):self.assertEqual(M.quarantine(A,"signature failure")["status"],"quarantined")
if __name__=="__main__":unittest.main()
