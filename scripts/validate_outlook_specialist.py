from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.outlook_specialist")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/advanced-outlook-specialist-policy.json").read_text());config=json.loads((ROOT/"config/agents/advanced-outlook-specialist.json").read_text());outlook=module();limits=policy["limits"]
 if (limits["maximum_diagnostics"],limits["maximum_hypotheses"],limits["maximum_rag_queries"],limits["maximum_remediation_proposals"],limits["minimum_root_cause_confidence"])!=(outlook.MAX_DIAGNOSTICS,outlook.MAX_HYPOTHESES,outlook.MAX_RAG_QUERIES,outlook.MAX_REMEDIATIONS,outlook.MIN_ROOT_CAUSE_CONFIDENCE):errors.append("Outlook limits mismatch")
 if set(config["allowed_tools"])!=set(outlook.READ_ONLY_TOOLS):errors.append("Outlook tool mismatch")
 if policy["requirements"]["remediation_is_proposal_only"] is not True:errors.append("remediation must remain proposal-only")
 catalog=json.loads((ROOT/"contracts/outlook-support-catalog.json").read_text())
 if set(catalog["clients"])!=set(policy["clients"]):errors.append("Outlook client catalogue mismatch")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("advanced Outlook specialist validation passed")
