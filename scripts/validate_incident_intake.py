from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.incident_intake")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/incident-intake-extraction-policy.json").read_text());config=json.loads((ROOT/"config/agents/incident-intake-extractor.json").read_text());intake=module();limits=policy["limits"]
 expected=(intake.MAX_SOURCE_CHARS,intake.MAX_SUMMARY_CHARS,intake.MAX_SYMPTOMS,intake.MAX_SYMPTOM_CHARS,intake.MAX_DOMAINS,intake.MAX_UNCERTAIN,intake.MAX_CLARIFICATIONS,intake.MAX_EVIDENCE_REFS);actual=(limits["maximum_source_characters"],limits["maximum_summary_characters"],limits["maximum_symptoms"],limits["maximum_symptom_characters"],limits["maximum_domain_candidates"],limits["maximum_uncertain_fields"],limits["maximum_clarification_needs"],limits["maximum_evidence_references"])
 if expected!=actual:errors.append("intake limits mismatch")
 if set(policy["enums"]["domains"])!=set(intake.DOMAINS) or set(policy["enums"]["business_impact"])!=set(intake.IMPACTS):errors.append("intake enums mismatch")
 if config["allowed_tools"]!=[]:errors.append("intake extractor must not use tools")
 if policy["safety"]["extractor_may_authorize_actions"] is not False:errors.append("extractor authority must be denied")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("incident intake validation passed")
