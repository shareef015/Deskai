from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.print_scan_specialist")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/advanced-print-scan-specialist-policy.json").read_text());config=json.loads((ROOT/"config/agents/advanced-print-scan-specialist.json").read_text());specialist=module();limits=policy["limits"]
 if (limits["maximum_diagnostics"],limits["maximum_hypotheses"],limits["maximum_rag_queries"],limits["maximum_remediation_proposals"],limits["minimum_root_cause_confidence"])!=(specialist.MAX_DIAGNOSTICS,specialist.MAX_HYPOTHESES,specialist.MAX_RAG_QUERIES,specialist.MAX_REMEDIATIONS,specialist.MIN_ROOT_CAUSE_CONFIDENCE):errors.append("print/scan limits mismatch")
 if set(config["allowed_tools"])!=set().union(*specialist.TOOLS.values()):errors.append("print/scan tools mismatch")
 if set(policy["topologies"])!=set(specialist.TOPOLOGIES):errors.append("topology mismatch")
 if policy["requirements"]["remediation_is_proposal_only"] is not True:errors.append("remediation must remain proposal-only")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("advanced printer and scanner specialist validation passed")
