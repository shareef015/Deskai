from __future__ import annotations
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/synthetic-conversation-generator-policy.json").read_text());path=ROOT/"data/synthetic/support-conversations.json";data=json.loads(path.read_text())
 spec=importlib.util.spec_from_file_location("generator",ROOT/"data/synthetic/generate_conversations.py");assert spec and spec.loader;generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
 if path.read_bytes()!=generator.canonical_bytes():errors.append("conversation dataset is not deterministic")
 conversations=data.get("conversations",[])
 if len(conversations)<policy["minimum_conversations"] or data.get("conversation_count")!=len(conversations):errors.append("conversation count is invalid")
 if len({c.get("conversation_id") for c in conversations})!=len(conversations):errors.append("conversation ids are not unique")
 states=set(policy["terminal_states"])
 if any(c.get("terminal_state") not in states or c.get("tenant_id")!=policy["tenant_id"] for c in conversations):errors.append("terminal state or tenant is invalid")
 if not any(c["decisions"]["diagnostic_consent"]=="declined" for c in conversations) or not any(c["decisions"]["remediation_approval"]=="rejected" for c in conversations):errors.append("decline or rejection branch missing")
 for conversation in conversations:
  turns=conversation.get("turns",[]);turn_states=[t.get("state") for t in turns]
  if any(state not in turn_states for state in policy["required_states"]):errors.append("required journey state missing");break
  if not turns or "How can I help you?" not in turns[0].get("text",""):errors.append("greeting is invalid");break
  if conversation["terminal_state"]=="resolved" and conversation["decisions"]["employee_confirmation"]!="confirmed":errors.append("resolution lacks employee confirmation");break
  if conversation["decisions"]["diagnostic_consent"]=="declined" and any(t["state"]=="diagnosing" for t in turns):errors.append("diagnostics occurred after declined consent");break
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("synthetic conversation and employee-response validation passed")
