from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate()->list[str]:
 p=json.loads((ROOT/"contracts/synthetic-control-policy.json").read_text());errors=[];req=p["requirements"]
 for key in ("authenticated_operator","synthetic_mode_required","server_bound_tenant","predefined_scenarios_only","expected_version_required","snapshot_before_fault","rollback_supported","all_mutations_audited","llm_cannot_operate_panel"):
  if req.get(key) is not True:errors.append(f"control missing: {key}")
 if req["production_enabled"] if "production_enabled" in req else p.get("production_enabled",False):errors.append("synthetic panel enabled in production")
 service=(ROOT/"services/api/src/deskpilot_api/synthetic/control.py").read_text();routes=(ROOT/"services/api/src/deskpilot_api/routes/synthetic_control.py").read_text();ui=(ROOT/"apps/web/src/app/synthetic-control/page.tsx").read_text()
 for token in ("operator.is_ai","tenant_administrator","expected_version","RESET SYNTHETIC TENANT","capture_snapshot"):
  if token not in service:errors.append(f"service invariant missing: {token}")
 for route in ('/activate','/rollback','/reset','/compare','/snapshots'):
  if route not in routes:errors.append(f"route missing: {route}")
 if "window.prompt" in ui or "window.alert" in ui or "Synthetic demo only" not in ui:errors.append("unsafe control panel UI")
 return errors
if __name__=="__main__":
 e=validate()
 if e:raise SystemExit("\n".join(e))
 print("synthetic control panel validation passed")
