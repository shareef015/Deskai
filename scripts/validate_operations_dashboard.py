from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.operations_dashboard")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/operations-dashboard-policy.json").read_text());config=json.loads((ROOT/"config/agents/operations-dashboard.json").read_text());m=module();ui=(ROOT/"apps/web/src/app/operations/page.tsx").read_text()
 if policy["requirements"].get("bounded_queue")!=m.MAX_QUEUE or config.get("maximum_queue_rows")!=m.MAX_QUEUE:errors.append("queue bound drift")
 if config.get("environment_mix_allowed") is not False:errors.append("live and synthetic mixing enabled")
 for marker in ("Synthetic recruiter dashboard","Live authorized tenant","SLA at risk","Stalled runs","Approval backlog","Rollback alert",'role="status"'):
  if marker not in ui:errors.append(f"operations UI marker missing: {marker}")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("operations dashboard validation passed")
