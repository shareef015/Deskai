from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.evaluation_release_gate")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/evaluation-release-gate-policy.json").read_text());config=json.loads((ROOT/"config/agents/evaluation-release-gates.json").read_text());ui=(ROOT/"apps/web/src/app/evaluation-gates/page.tsx").read_text();module()
 for key in ("immutable_baseline","domain_scenario_slices","regression_budgets","blocker_classification","blocked_release_cannot_approve","exact_run_concurrency"):
  if policy["requirements"].get(key) is not True:errors.append(f"evaluation control disabled: {key}")
 if not config.get("blocking_metrics"):errors.append("blocking metrics missing")
 for marker in ("Recruiter-safe synthetic evaluation","Baseline comparison","Release blocked","Blocking regression","Release evidence"):
  if marker not in ui:errors.append(f"evaluation UI marker missing: {marker}")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("evaluation release gate validation passed")
