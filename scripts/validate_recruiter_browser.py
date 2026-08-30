from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.demo_browser_evidence")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/recruiter-browser-validation-policy.json").read_text());config=json.loads((ROOT/"config/agents/recruiter-browser-validation.json").read_text());spec=(ROOT/"tests/browser/recruiter-demo.spec.ts").read_text();ui=(ROOT/"apps/web/src/app/incident-workspace/conversation-panel.tsx").read_text();module()
 for key in ("real_browser_execution","full_success_journey","remote_decline_branch","failed_verification_branch","deterministic_reset","desktop_screenshot","mobile_screenshot","keyboard_navigation","mobile_drawer","dashboard_validation","console_error_check","evidence_hashes"):
  if policy["requirements"].get(key) is not True:errors.append(f"browser validation control disabled: {key}")
 for marker in ("Follow-up question 1 of 2","Allow remote access","Approve this repair","Is the issue working now?","Reset demonstration"):
  if marker not in ui:errors.append(f"journey marker missing: {marker}")
 for marker in ("conversation-success","remote-decline","failed-verification","insights-dashboard","mobile-drawer","keyboard-focus","deterministic-reset"):
  if marker not in spec:errors.append(f"browser scenario missing: {marker}")
 manifest=ROOT/"evidence/browser/run-manifest.json"
 if manifest.exists():
  data=json.loads(manifest.read_text())
  if data.get("result")!="passed" or data.get("console_error_count")!=0:errors.append("browser evidence did not pass")
 if config.get("external_side_effects") is not False:errors.append("demo browser can cause external side effects")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("Recruiter browser validation contract passed")
