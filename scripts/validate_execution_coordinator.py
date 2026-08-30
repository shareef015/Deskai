from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.execution_coordinator")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/governed-remediation-execution-policy.json").read_text());config=json.loads((ROOT/"config/agents/governed-remediation-execution-coordinator.json").read_text());executor=module();limits=policy["limits"]
 if (limits["maximum_token_ttl_seconds"],limits["maximum_action_deadline_seconds"],limits["maximum_plan_actions"])!=(executor.MAX_TOKEN_TTL_SECONDS,executor.MAX_ACTION_DEADLINE_SECONDS,executor.MAX_PLAN_ACTIONS):errors.append("execution limits mismatch")
 if set(policy["prohibited_capabilities"])!=set(executor.PROHIBITED_CAPABILITIES):errors.append("prohibited capability mismatch")
 if config["allowed_tools"]!=["governed_capability_gateway"] or policy["requirements"]["raw_command_surface"] is not False:errors.append("execution boundary invalid")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("governed remediation execution validation passed")
