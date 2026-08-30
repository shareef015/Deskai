from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.parallel_diagnostics")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/parallel-diagnostics-policy.json").read_text());fan=module()
 if policy["fanout"]["maximum_branches"]!=fan.MAX_BRANCHES:errors.append("branch limit mismatch")
 if policy["fanout"]["branch_timeout_seconds"]!=fan.BRANCH_TIMEOUT_SECONDS:errors.append("timeout mismatch")
 if policy["reducer"]["maximum_evidence_records"]!=fan.MAX_EVIDENCE:errors.append("evidence limit mismatch")
 if policy["fanout"]["side_effects"]!="read_only":errors.append("fanout must be read-only")
 if policy["reducer"]["preserve_contradictions"] is not True:errors.append("contradictions must be preserved")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("parallel diagnostics validation passed")
