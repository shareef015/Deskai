from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PAGE=ROOT/"apps/web/src/app/incident-workspace/page.tsx";TYPES=ROOT/"apps/web/src/app/incident-workspace/workspace-types.ts";CSS=ROOT/"apps/web/src/app/globals.css"
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/incident-workspace-ui-policy.json").read_text());source=PAGE.read_text();types=TYPES.read_text();css=CSS.read_text()
 required={"explicit_live_synthetic_boundary","typed_runtime_events","event_field_allowlist","durable_cursor_reconnect","duplicate_event_suppression","bounded_timeline","privacy_safe_evidence_references","human_interrupt_form","no_prompt_or_alert","accessible_status_updates","responsive_layout"}
 if any(policy["requirements"].get(key) is not True for key in required):errors.append("workspace control disabled")
 for marker in ("after_cursor=${state.lastCursor}","event.cursor<=state.lastCursor","slice(-100)","ALLOWED_FIELDS",'aria-live="polite"',"Synthetic recruiter demonstration","Live authorized tenant"):
  if marker not in source:errors.append(f"workspace marker missing: {marker}")
 if "window.prompt" in source or "alert(" in source:errors.append("blocking browser dialog prohibited")
 for marker in ("SafeRuntimeEvent","WorkspaceMode","InterruptView"):
  if marker not in types:errors.append(f"typed contract missing: {marker}")
 if "@media(max-width:800px)" not in css or "prefers-reduced-motion" not in css:errors.append("responsive or motion accessibility missing")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("incident workspace UI validation passed")
