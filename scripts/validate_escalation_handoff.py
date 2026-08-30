from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.escalation_handoff")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/human-escalation-handoff-policy.json").read_text());config=json.loads((ROOT/"config/agents/human-escalation-ownership-handoff.json").read_text());handoff=module();limits=policy["limits"]
 if (limits["maximum_handoff_hops"],limits["maximum_evidence_references"])!=(handoff.MAX_HANDOFF_HOPS,handoff.MAX_EVIDENCE_REFS):errors.append("handoff limits mismatch")
 if config["allowed_tools"]!=[]:errors.append("handoff agent must not have tools")
 if any(policy["authority"][key] is not False for key in policy["authority"]):errors.append("handoff authority boundary invalid")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("human escalation and ownership-handoff validation passed")
