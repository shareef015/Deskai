from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.approval_validation")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/human-approval-decision-policy.json").read_text());config=json.loads((ROOT/"config/agents/human-approval-decision-validator.json").read_text());approval=module()
 if policy["maximum_ttl_minutes"]!=approval.MAX_APPROVAL_TTL_MINUTES:errors.append("approval TTL mismatch")
 if config["allowed_tools"]!=[]:errors.append("approval validator must not have tools")
 if policy["requirements"]["ai_approval_authority"] is not False or policy["requirements"]["execution_authority"] is not False:errors.append("approval authority boundary invalid")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("human approval request and decision validation passed")
