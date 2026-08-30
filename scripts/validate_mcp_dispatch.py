from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.mcp_dispatch")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/governed-mcp-dispatch-policy.json").read_text());m=module()
 if policy["limits"]["maximum_envelope_ttl_seconds"]!=m.MAX_ENVELOPE_TTL_SECONDS:errors.append("MCP envelope TTL mismatch")
 if not all(policy["requirements"][k] is True for k in ("prior_tool_authorization","nonce_single_use","typed_result_allowlist","quarantine_noncompliant_agent")):errors.append("MCP security requirements missing")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("governed MCP dispatch validation passed")
