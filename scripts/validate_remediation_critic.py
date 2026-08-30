from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.remediation_critic")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/remediation-safety-critic-policy.json").read_text());config=json.loads((ROOT/"config/agents/remediation-safety-policy-critic.json").read_text());critic=module()
 if (policy["limits"]["maximum_actions"],policy["limits"]["maximum_findings"])!=(critic.MAX_ACTIONS,critic.MAX_FINDINGS):errors.append("critic limits mismatch")
 if config["allowed_tools"]!=[]:errors.append("critic must not have tools")
 if any(policy["requirements"][key] is not False for key in ("plan_rewrite_authority","approval_authority","execution_authority")):errors.append("critic authority boundary invalid")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("remediation safety and policy-critic validation passed")
