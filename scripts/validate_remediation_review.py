from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.remediation_review")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/remediation-review-policy.json").read_text());config=json.loads((ROOT/"config/agents/remediation-review.json").read_text());ui=(ROOT/"apps/web/src/app/remediation-review/page.tsx").read_text();module()
 required=("immutable_plan","plan_digest_binding","acyclic_dependencies","rollback_for_medium_high","segregation_of_duties","expiry_enforcement","partial_failure_route")
 if any(policy["requirements"].get(key) is not True for key in required):errors.append("remediation review control disabled")
 if config.get("medium_high_rollback_required") is not True:errors.append("rollback requirement disabled")
 for marker in ("Before","After","Rollback:","Independent decision","Approve this exact plan","Partial failure"):
  if marker not in ui:errors.append(f"review UI marker missing: {marker}")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("remediation review validation passed")
