from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.remediation_planner")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/risk-aware-remediation-planning-policy.json").read_text());config=json.loads((ROOT/"config/agents/risk-aware-remediation-planner.json").read_text());planner=module()
 if (policy["limits"]["maximum_candidate_actions"],policy["limits"]["maximum_planned_actions"])!=(planner.MAX_CANDIDATES,planner.MAX_ACTIONS):errors.append("remediation limits mismatch")
 if set(policy["prohibited_actions"])!=set(planner.PROHIBITED_ACTIONS):errors.append("prohibited action mismatch")
 if config["allowed_tools"]!=[] or policy["requirements"]["execution_authority"] is not False:errors.append("planner must remain non-executing")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("risk-aware remediation-planner validation passed")
