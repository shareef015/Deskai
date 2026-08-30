from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.remote_support_session")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/continuous-remote-support-policy.json").read_text());config=json.loads((ROOT/"config/agents/continuous-remote-support.json").read_text());ui=(ROOT/"apps/web/src/app/incident-workspace/conversation-panel.tsx").read_text();module()
 for key in ("continuous_conversation","follow_up_questions_visible","device_confirmation_before_access","employee_remote_access_permission","scoped_capabilities","short_lived_session","revocable_access","ui_mode_only","change_approval_separate","technical_verification","employee_confirmation","continue_until_resolved_or_escalated"):
  if policy["requirements"].get(key) is not True:errors.append(f"remote support control disabled: {key}")
 for marker in ("Follow-up question","Request remote access","Allow remote access","Decline","UI-mode support session","Approve this repair","Revoke remote access","Is the issue working now?","Issue resolved"):
  if marker not in ui:errors.append(f"conversation flow marker missing: {marker}")
 if config.get("unattended_access") is not False:errors.append("unattended access enabled")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("Continuous remote support validation passed")
