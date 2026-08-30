from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.advanced_investigation")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/advanced-investigation-policy.json").read_text());config=json.loads((ROOT/"config/agents/advanced-investigation.json").read_text());ui=(ROOT/"apps/web/src/app/advanced-investigation/page.tsx").read_text();shell=(ROOT/"apps/web/src/components/app-shell.tsx").read_text();module()
 for key in ("role_gated","diagnostic_consent_required","tenant_scoped","evidence_grounded_graph","bounded_graph","deterministic_ordering","retrieval_provenance","agent_trace_provenance","specialist_summary_only","route_ownership_complete"):
  if policy["requirements"].get(key) is not True:errors.append(f"advanced investigation control disabled: {key}")
 for marker in ("Evidence graph","Retrieval evidence","Agent trace","Specialist diagnostics","Read-only investigation","Evidence IDs"):
  if marker not in ui:errors.append(f"advanced UI marker missing: {marker}")
 for route in ("/advanced-investigation","/knowledge-review","/action-center"):
  if route not in shell:errors.append(f"owned route missing from shell: {route}")
 page_routes={"/" if p.parent==ROOT/"apps/web/src/app" else "/"+str(p.parent.relative_to(ROOT/"apps/web/src/app")).replace("\\","/") for p in (ROOT/"apps/web/src/app").rglob("page.tsx")};owned={"/","/login"};
 import re
 owned.update(re.findall(r'"(/[a-z0-9-]+)"',shell))
 for route in sorted(page_routes-owned):errors.append(f"orphan page: {route}")
 if config.get("mutation_tools_allowed") is not False:errors.append("advanced workspace mutation enabled")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("Advanced investigation and route ownership validation passed")
