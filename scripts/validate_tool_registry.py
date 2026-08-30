from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.tool_registry")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/tool-least-privilege-policy.json").read_text());m=module()
 if set(policy["prohibited_parameter_keys"])!=set(m.PROHIBITED_PARAMETER_KEYS):errors.append("tool parameter prohibition mismatch")
 if policy["requirements"]["dynamic_tools"] is not False or policy["requirements"]["raw_commands"] is not False:errors.append("tool registry boundary invalid")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("tool least-privilege capability-registry validation passed")
