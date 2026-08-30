from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.incident_closure")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/incident-closure-policy.json").read_text());config=json.loads((ROOT/"config/agents/incident-closure.json").read_text());ui=(ROOT/"apps/web/src/app/incident-closure/page.tsx").read_text();module()
 for key in ("technical_verification","employee_confirmation","immutable_closure","SLA_outcome","governed_reopen_reasons","regression_evidence_required","deterministic_audit_digest"):
  if policy["requirements"].get(key) is not True:errors.append(f"closure control disabled: {key}")
 if config.get("knowledge_publication")!="separate_human_review":errors.append("automatic knowledge publication enabled")
 for marker in ("Closure eligibility","Employee confirmation","immutable closure record","Reopen with regression evidence","Export incident audit"):
  if marker not in ui:errors.append(f"closure UI marker missing: {marker}")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("incident closure validation passed")
