from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.clarification")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/context-aware-clarification-policy.json").read_text());config=json.loads((ROOT/"config/agents/context-aware-clarification.json").read_text());clar=module();limits=policy["limits"]
 if (limits["maximum_questions_per_turn"],limits["maximum_rounds"],limits["maximum_question_characters"],limits["maximum_candidate_needs"])!=(clar.MAX_QUESTIONS,clar.MAX_ROUNDS,clar.MAX_QUESTION_CHARS,clar.MAX_NEEDS):errors.append("clarification limits mismatch")
 if policy["priority_order"]!=list(clar.PRIORITY):errors.append("priority mismatch")
 if config["allowed_tools"]!=[]:errors.append("clarification agent must not use tools")
 for key in ("agent_has_tools","agent_may_diagnose","agent_may_request_secrets","agent_may_authorize_actions"):
  if policy["safety"][key] is not False:errors.append(f"{key} must be false")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("context-aware clarification validation passed")
