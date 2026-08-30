from __future__ import annotations
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/synthetic-remediation-execution-policy.json").read_text());path=ROOT/"data/synthetic/remediation-scenarios.json";data=json.loads(path.read_text())
 spec=importlib.util.spec_from_file_location("generator",ROOT/"data/synthetic/generate_remediation_scenarios.py");assert spec and spec.loader;generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
 if path.read_bytes()!=generator.canonical_bytes():errors.append("remediation scenarios are not deterministic")
 scenarios=data.get("scenarios",[])
 if len(scenarios)<policy["minimum_scenarios"] or data.get("scenario_count")!=len(scenarios):errors.append("scenario count is invalid")
 if len({s.get("scenario_id") for s in scenarios})!=len(scenarios) or len({s.get("idempotency_key") for s in scenarios})!=len(scenarios):errors.append("scenario or idempotency ids are not unique")
 if set(policy["outcomes"])!={s.get("outcome") for s in scenarios}:errors.append("execution outcome coverage is incomplete")
 for scenario in scenarios:
  plan=scenario.get("plan",{});attempts=scenario.get("attempts",[]);rollback=scenario.get("rollback_result",{});final=scenario.get("final_state",{})
  if not plan.get("authorization_valid") or not plan.get("precondition_digest") or not plan.get("typed_action_id"):errors.append("plan authorization or pre-state is incomplete");break
  if len(attempts)>policy["maximum_attempts"] or any(a.get("duration_ms",0)>policy["maximum_duration_ms"] for a in attempts):errors.append("attempt bounds exceeded");break
  if scenario["outcome"] in {"partial_rollback_success","timeout_compensated"} and (not rollback.get("attempted") or not rollback.get("verification_passed") or rollback.get("observed_post_rollback_digest")!=final.get("pre_state_digest")):errors.append("verified rollback is invalid");break
  if scenario["outcome"]=="partial_rollback_failed" and (not final.get("safe_escalation_required") or rollback.get("status")!="failed"):errors.append("rollback failure did not escalate");break
  if scenario["outcome"]=="duplicate_idempotent_replay" and (len(attempts)!=2 or attempts[1].get("status")!="deduplicated" or attempts[1].get("state_changed")):errors.append("idempotent replay is invalid");break
  if "powershell" in plan.get("typed_action_id","").lower() or "shell" in plan.get("typed_action_id","").lower():errors.append("unrestricted action surface found");break
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("synthetic remediation, failure and rollback validation passed")
