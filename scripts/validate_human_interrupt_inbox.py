from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.human_interrupts")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/human-interrupt-inbox-policy.json").read_text());config=json.loads((ROOT/"config/agents/human-interrupt-inbox.json").read_text())
 required={"authenticated_tenant_scope","role_scoped_queue","employee_subject_binding","segregation_of_duties","safe_review_packet_allowlist","optimistic_checkpoint_concurrency","expiry_enforcement","idempotent_decisions","terminal_immutability","durable_monotonic_events"}
 if not required<=set(policy.get("requirements",{})):errors.append("required policy controls missing")
 if any(policy["requirements"].get(key) is not True for key in required):errors.append("required policy control disabled")
 if config.get("review_packet_mode")!="privacy_safe_references":errors.append("unsafe review packet mode")
 if config.get("decision_idempotency")!="required":errors.append("decision idempotency not required")
 source=(ROOT/"services/api/src/deskpilot_api/human_interrupts.py").read_text()
 for marker in ("self approval denied","checkpoint concurrency mismatch","interrupt expired","SAFE_PACKET_FIELDS","events_after"):
  if marker not in source:errors.append(f"runtime marker missing: {marker}")
 module();return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("human interrupt inbox validation passed")
