from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.evidence_explorer")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/evidence-explorer-policy.json").read_text());config=json.loads((ROOT/"config/agents/evidence-explorer.json").read_text());m=module();ui=(ROOT/"apps/web/src/app/evidence-explorer/page.tsx").read_text()
 if policy["requirements"].get("bounded_results")!=m.MAX_ITEMS or config.get("maximum_items")!=m.MAX_ITEMS:errors.append("evidence bound drift")
 if policy["requirements"].get("raw_endpoint_content") is not False or config.get("raw_content_export") is not False:errors.append("raw evidence exposure enabled")
 for marker in ("Contradictions only","Technical details and lineage","freshness","Supervisor handoff","Export {selected.length} selected references"):
  if marker not in ui:errors.append(f"evidence UI marker missing: {marker}")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("evidence explorer validation passed")
