from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.application_shell")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/application-shell-policy.json").read_text());config=json.loads((ROOT/"config/agents/application-shell.json").read_text());shell=(ROOT/"apps/web/src/components/app-shell.tsx").read_text();module()
 for key in ("authenticated_shell","tenant_context_visible","live_synthetic_mode_visible","role_filtered_navigation","grouped_navigation","mobile_drawer","keyboard_accessible","breadcrumb_landmark","route_change_closes_drawer","loading_error_empty_states"):
  if policy["requirements"].get(key) is not True:errors.append(f"shell control disabled: {key}")
 if config.get("mode_isolation") is not True or config.get("role_filter_source")!="authenticated_session":errors.append("unsafe navigation source")
 for marker in ("Skip to main content","aria-label=\"Primary navigation\"","aria-label=\"Breadcrumb\"","Synthetic demo","aria-expanded","Escape"):
  if marker not in shell:errors.append(f"application shell marker missing: {marker}")
 for path in (ROOT/"apps/web/src/app/loading.tsx",ROOT/"apps/web/src/app/error.tsx",ROOT/"apps/web/src/components/empty-state.tsx"):
  if not path.exists():errors.append(f"state component missing: {path.name}")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("Application shell validation passed")
