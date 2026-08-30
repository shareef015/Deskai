from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.agent_observability")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/agent-observability-policy.json").read_text());config=json.loads((ROOT/"config/agents/agent-observability.json").read_text());obs=module();limits=policy["limits"]
 if (limits["maximum_events_per_trace"],limits["maximum_attribute_keys"],limits["maximum_attribute_value_characters"])!=(obs.MAX_EVENTS_PER_TRACE,obs.MAX_ATTRIBUTE_KEYS,obs.MAX_ATTRIBUTE_VALUE_CHARS):errors.append("trace limits mismatch")
 if set(config["allowed_attributes"])!=set(obs.ALLOWED_ATTRIBUTES):errors.append("trace allowlist mismatch")
 if policy["content_policy"]["prompts_and_responses_stored_by_default"] is not False or policy["requirements"]["audit_reference_not_audit_replacement"] is not True:errors.append("trace privacy or audit boundary invalid")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("agent decision trace and observability validation passed")
