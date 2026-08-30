from __future__ import annotations
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/synthetic-consent-approval-policy.json").read_text());path=ROOT/"data/synthetic/consent-approval-scenarios.json";data=json.loads(path.read_text())
 spec=importlib.util.spec_from_file_location("generator",ROOT/"data/synthetic/generate_consent_approval_scenarios.py");assert spec and spec.loader;generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
 if path.read_bytes()!=generator.canonical_bytes():errors.append("authorization scenarios are not deterministic")
 scenarios=data.get("scenarios",[])
 if len(scenarios)<policy["minimum_scenarios"] or data.get("scenario_count")!=len(scenarios):errors.append("scenario count is invalid")
 if len({s.get("scenario_id") for s in scenarios})!=len(scenarios):errors.append("scenario ids are not unique")
 if set(policy["outcomes"])!={s.get("outcome") for s in scenarios}:errors.append("required authorization outcomes are incomplete")
 for scenario in scenarios:
  consent=scenario.get("consent",{});approval=scenario.get("approval",{});evaluation=scenario.get("evaluation",{})
  required={"tenant_id","employee_id","device_id","incident_id","session_id","purpose","capabilities","issued_at","expires_at"}
  if required-set(consent):errors.append("consent scope is incomplete");break
  if scenario["outcome"]!="authorized" and evaluation.get("execution_permitted") is not False:errors.append("denied scenario permitted execution");break
  if scenario["outcome"]=="authorized" and (not evaluation.get("diagnostic_authorized") or not evaluation.get("remediation_authorized")):errors.append("authorized path is incomplete");break
  if approval.get("requester_id")==approval.get("approver_id") and evaluation.get("remediation_authorized"):errors.append("self approval was accepted");break
  if approval.get("approver_role") in {"ai_service","auditor"} and evaluation.get("remediation_authorized"):errors.append("forbidden approver was accepted");break
  if not approval.get("pre_state_digest") or not approval.get("rollback") or len(evaluation.get("audit_event_ids",[]))!=2:errors.append("rollback or decision lineage missing");break
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("synthetic consent, approval and rejection validation passed")
