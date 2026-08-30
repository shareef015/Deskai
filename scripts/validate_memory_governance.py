from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.memory_governance")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/agent-memory-governance-policy.json").read_text());m=module()
 if policy["maximum_ttl_days"]!=m.MAX_TTL_DAYS:errors.append("memory TTL policy mismatch")
 if policy["requirements"]["hidden_memory"] is not False or policy["requirements"]["cross_incident_working_memory"] is not False or policy["requirements"]["automatic_model_summary_persistence"] is not False:errors.append("memory safety boundary invalid")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("agent memory governance validation passed")
