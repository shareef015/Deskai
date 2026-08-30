from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.agent_observability")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/agent-observability-dashboard-policy.json").read_text());config=json.loads((ROOT/"config/agents/agent-observability-dashboard.json").read_text());m=module();ui=(ROOT/"apps/web/src/app/agent-observability/page.tsx").read_text()
 if policy["requirements"].get("bounded_spans")!=m.MAX_SPANS or config.get("maximum_spans")!=m.MAX_SPANS:errors.append("span bound drift")
 if config.get("environment_mix_allowed") is not False or config.get("raw_payload_capture") is not False:errors.append("unsafe telemetry configuration")
 for marker in ("Synthetic recruiter telemetry","Live authorized tenant","Graph trace","Model tokens","Model cost","Quality and drift","Reliability controls"):
  if marker not in ui:errors.append(f"observability UI marker missing: {marker}")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("agent observability dashboard validation passed")
