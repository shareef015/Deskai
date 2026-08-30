from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.termination")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/deterministic-termination-policy.json").read_text());term=module();limits=policy["limits"]
 expected=(term.MAX_STEPS,term.MAX_REASONING_TURNS,term.MAX_PHASE_VISITS,term.MAX_IDENTICAL_STATE_VISITS,term.MAX_NO_PROGRESS);actual=(limits["maximum_graph_steps"],limits["maximum_reasoning_turns"],limits["maximum_visits_per_phase"],limits["maximum_identical_state_visits"],limits["maximum_no_progress_transitions"])
 if expected!=actual:errors.append("termination limits mismatch")
 if set(policy["terminal_states"])!=set(term.TERMINALS):errors.append("terminal state mismatch")
 for key in ("terminal_states_immutable","abstention_is_safe","termination_proof_required"):
  if policy["safety"][key] is not True:errors.append(f"{key} required")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("deterministic termination validation passed")
