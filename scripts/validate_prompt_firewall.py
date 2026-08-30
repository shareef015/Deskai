from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.prompt_firewall")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/prompt-firewall-policy.json").read_text());config=json.loads((ROOT/"config/agents/prompt-firewall.json").read_text());m=module()
 if policy["limits"]["maximum_content_characters"]!=m.MAX_CONTENT_CHARS or config["trust_rank"]!=m.TRUST_RANK:errors.append("prompt-firewall policy mismatch")
 if set(config["prohibited_tool_keys"])!=set(m.PROHIBITED_TOOL_KEYS) or policy["requirements"]["raw_command_arguments"] is not False:errors.append("tool argument boundary mismatch")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("prompt firewall and untrusted-content isolation validation passed")
