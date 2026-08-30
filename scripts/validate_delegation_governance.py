from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.delegation_governance")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/multi-agent-delegation-policy.json").read_text());m=module();limits=policy["limits"]
 if (limits["maximum_delegation_depth"],limits["maximum_fanout"],limits["maximum_child_tool_calls"],limits["maximum_child_tokens"],limits["maximum_child_seconds"])!=(m.MAX_DELEGATION_DEPTH,m.MAX_FANOUT,m.MAX_CHILD_TOOL_CALLS,m.MAX_CHILD_TOKENS,m.MAX_CHILD_SECONDS):errors.append("delegation limits mismatch")
 if set(policy["non_delegable_authorities"])!=set(m.NON_DELEGABLE_AUTHORITIES):errors.append("non-delegable authority mismatch")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("multi-agent delegation governance validation passed")
