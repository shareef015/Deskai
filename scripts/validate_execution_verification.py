from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.execution_verification")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/execution-verification-policy.json").read_text());config=json.loads((ROOT/"config/agents/execution-verification.json").read_text());ui=(ROOT/"apps/web/src/app/execution-verification/page.tsx").read_text();module()
 for key in ("single_use_token","pre_state_required","partial_failure_stops","rollback_verification","rollback_failure_escalates","employee_confirmation"):
  if policy["requirements"].get(key) is not True:errors.append(f"execution control disabled: {key}")
 if config.get("rollback_failure_route")!="human_recovery":errors.append("unsafe rollback failure route")
 for marker in ("Live action progress","Pre-state captured","single-use capability token","partial failure","Employee outcome",'role="status"'):
  if marker not in ui:errors.append(f"execution UI marker missing: {marker}")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("execution verification validation passed")
