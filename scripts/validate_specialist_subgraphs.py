from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.specialist_subgraphs")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/specialist-subgraph-policy.json").read_text());sub=module()
 if set(policy["specialists"])!=set(sub.TOOLS):errors.append("specialist set mismatch")
 for domain,config in policy["specialists"].items():
  if set(config["tools"])!=set(sub.TOOLS[domain]):errors.append(f"tool mismatch: {domain}")
 limits=policy["limits"]
 if (limits["maximum_steps"],limits["maximum_tool_calls"],limits["maximum_retrieval_rounds"],limits["maximum_evidence_records"])!=(sub.MAX_STEPS,sub.MAX_TOOL_CALLS,sub.MAX_RETRIEVAL_ROUNDS,sub.MAX_EVIDENCE):errors.append("limit mismatch")
 for denied in ("specialist_may_remediate","specialist_may_approve","specialist_may_close_incident"):
  if policy["boundaries"][denied] is not False:errors.append(f"{denied} must be false")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("specialist subgraph validation passed")
