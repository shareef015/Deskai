from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.human_handoff")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/human-handoff-policy.json").read_text());config=json.loads((ROOT/"config/agents/human-handoff.json").read_text());ui=(ROOT/"apps/web/src/app/human-handoff/page.tsx").read_text();module()
 for key in ("safe_packet_allowlist","SLA_state","single_owner_custody","immutable_custody_history","post_change_verification","controlled_agent_return"):
  if policy["requirements"].get(key) is not True:errors.append(f"handoff control disabled: {key}")
 if config.get("human_change_requires_verification") is not True:errors.append("human verification disabled")
 for marker in ("SLA acknowledgement","Immutable custody history","Acknowledge and accept custody","Record change and require verification","Return to agent verification"):
  if marker not in ui:errors.append(f"handoff UI marker missing: {marker}")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("human handoff validation passed")
