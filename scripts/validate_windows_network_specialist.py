from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.windows_network_specialist")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/advanced-windows-network-specialist-policy.json").read_text());config=json.loads((ROOT/"config/agents/advanced-windows-network-specialist.json").read_text());specialist=module();limits=policy["limits"]
 if (limits["maximum_diagnostics"],limits["maximum_hypotheses"],limits["maximum_rag_queries"],limits["maximum_remediation_proposals"],limits["minimum_root_cause_confidence"])!=(specialist.MAX_DIAGNOSTICS,specialist.MAX_HYPOTHESES,specialist.MAX_RAG_QUERIES,specialist.MAX_REMEDIATIONS,specialist.MIN_ROOT_CAUSE_CONFIDENCE):errors.append("Windows/network limits mismatch")
 if set(config["allowed_tools"])!=set(specialist.TOOLS):errors.append("Windows/network tools mismatch")
 if policy["requirements"]["remediation_is_proposal_only"] is not True:errors.append("remediation must remain proposal-only")
 if not specialist.SECURITY_BOUNDARIES:errors.append("security boundaries missing")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("advanced Windows and network specialist validation passed")
