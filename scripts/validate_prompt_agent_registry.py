from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.prompt_registry")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/prompt-agent-registry-policy.json").read_text());migration=(ROOT/"services/api/migrations/versions/0014_prompt_agent_registry.py").read_text()
 if policy["evaluation_gates"]!={"minimum_groundedness":.9,"minimum_task_success":.85,"minimum_safety":.99,"maximum_regression_rate":.02}:errors.append("evaluation gates mismatch")
 for key in ("secrets_in_prompts","llm_may_self_modify_configuration","unapproved_activation","silent_substitution"):
  if policy["safety"][key] is not False:errors.append(f"{key} must be false")
 for token in ("ai_configuration_artifacts","ai_configuration_approvals","ai_configuration_deployments","FORCE ROW LEVEL SECURITY"):
  if token not in migration:errors.append(f"migration missing {token}")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("prompt and agent registry validation passed")
