from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.conversation_supervisor")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/conversation-supervisor-policy.json").read_text());config=json.loads((ROOT/"config/agents/conversation-supervisor.json").read_text());conv=module()
 limits=policy["limits"]
 if (limits["maximum_conversation_turns"],limits["maximum_question_count_per_response"],limits["maximum_response_characters"],limits["maximum_summary_characters"])!=(conv.MAX_TURNS,conv.MAX_QUESTIONS,conv.MAX_RESPONSE_CHARS,conv.MAX_SUMMARY_CHARS):errors.append("conversation limits mismatch")
 if config["allowed_tools"]!=[]:errors.append("conversation agent must not use tools")
 required={"role","objective","input_schema_version","output_schema_version","evidence_priority","allowed_tools","prohibited_actions","rag_policy","confidence_behavior","clarification_policy","citation_rules","risk_and_approval_rules","budgets","failure_handling","escalation_behavior","examples","counterexamples","evaluation_provenance"}
 if not required<=set(config):errors.append("prompt contract incomplete")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("conversation supervisor validation passed")
