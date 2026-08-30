from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.planning_governance")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/agent-planning-governance-policy.json").read_text());m=module();limits=policy["limits"]
 if (limits["maximum_plan_steps"],limits["maximum_replans"],limits["maximum_tool_calls"],limits["maximum_plan_tokens"],limits["maximum_plan_duration_seconds"])!=(m.MAX_PLAN_STEPS,m.MAX_REPLANS,m.MAX_TOOL_CALLS,m.MAX_PLAN_TOKENS,m.MAX_PLAN_DURATION_SECONDS):errors.append("planning limits mismatch")
 if set(policy["forbidden_goals"])!=set(m.FORBIDDEN_GOALS) or policy["requirements"]["silent_plan_mutation"] is not False:errors.append("planning safety boundary mismatch")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("agent planning governance validation passed")
