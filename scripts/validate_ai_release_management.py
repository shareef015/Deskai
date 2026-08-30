from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.ai_release_management")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/ai-release-management-policy.json").read_text());config=json.loads((ROOT/"config/agents/ai-release-management.json").read_text());ui=(ROOT/"apps/web/src/app/release-management/page.tsx").read_text();module()
 for key in ("immutable_bundle_versions","compatibility_matrix","independent_approval","staged_canary_rollout","approved_rollback_target","emergency_freeze","append_only_deployment_events"):
  if policy["requirements"].get(key) is not True:errors.append(f"release control disabled: {key}")
 if config.get("environment_mix_allowed") is not False:errors.append("environment mixing enabled")
 for marker in ("Compatibility matrix","Evaluation evidence","Deployment provenance","Canary traffic","Freeze automated rollout","Rollback to prior bundle"):
  if marker not in ui:errors.append(f"release UI marker missing: {marker}")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("AI release management validation passed")
