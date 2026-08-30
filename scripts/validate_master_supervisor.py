from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def modules():return importlib.import_module("deskpilot_ai.state"),importlib.import_module("deskpilot_ai.supervisor")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/master-service-desk-supervisor-policy.json").read_text());state,supervisor=modules();sample=state.new_state({"tenant_id":"t","incident_id":"i","thread_id":"x","correlation_id":"c","employee_id":"e","device_id":"d","initial_message":"help"})
 if policy["entry_node"]!="greeting":errors.append("unexpected entry node")
 if set(policy["terminal_nodes"])!=set(supervisor.TERMINAL_PHASES):errors.append("terminal mismatch")
 if policy["limits"]["maximum_graph_steps"]!=state.MAX_GRAPH_STEPS:errors.append("step budget mismatch")
 if policy["safety_invariants"]["llm_may_authorize_actions"] is not False:errors.append("LLM authority must be denied")
 if not {"tenant_id","incident_id","thread_id","correlation_id"}<=set(sample):errors.append("state scope missing")
 source=(ROOT/"services/ai-service/src/deskpilot_ai/supervisor.py").read_text()
 for token in ("capability_token_missing","human_consent_required","human_approval_required","employee_confirmation_required"):
  if token not in source:errors.append(f"missing invariant {token}")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("master service desk supervisor validation passed")
