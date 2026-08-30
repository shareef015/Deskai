from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.agent_runtime")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/agent-runtime-api-policy.json").read_text());config=json.loads((ROOT/"config/agents/agent-runtime-api.json").read_text());m=module()
 if set(config["public_event_fields"])!=set(m.ALLOWED_EVENT_FIELDS):errors.append("runtime event allowlist mismatch")
 if policy["requirements"]["raw_prompt_or_endpoint_content"] is not False or policy["requirements"]["terminal_immutability"] is not True:errors.append("runtime privacy or terminal boundary invalid")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("real-time agent execution API validation passed")
