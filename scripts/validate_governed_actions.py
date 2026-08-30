from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.governed_actions")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/governed-action-ui-policy.json").read_text());config=json.loads((ROOT/"config/agents/governed-actions.json").read_text());ui=(ROOT/"apps/web/src/components/governed-action-surface.tsx").read_text();module()
 for key in ("typed_action_schemas","server_validation","role_and_scope_check","stale_context_check","duplicate_submission_denied","secret_content_denied","accessible_modal","accessible_drawer","focus_restoration","escape_cancellation","explicit_confirmation","submission_states"):
  if policy["requirements"].get(key) is not True:errors.append(f"action control disabled: {key}")
 for marker in ('role="dialog"','aria-modal="true"','aria-describedby','Escape','Confirm submission','Submitting…','focus()'):
  if marker not in ui:errors.append(f"action surface marker missing: {marker}")
 for path in (ROOT/"apps/web/src").rglob("*.tsx"):
  text=path.read_text()
  if "window.prompt" in text or "window.alert" in text:errors.append(f"browser dialog remains: {path.relative_to(ROOT)}")
 if config.get("double_submit_prevention") is not True:errors.append("double submission protection disabled")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("Governed action surfaces validation passed")
