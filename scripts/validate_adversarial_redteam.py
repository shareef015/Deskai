from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.adversarial_evaluation")
def oracle(cases,m):return tuple(m.AttackResult(c.attack_id,c.expected_behavior=="block",c.expected_behavior=="abstain",c.expected_behavior=="escalate",False,False,False,False,c.expected_audit_code,"a"*64,"a"*64) for c in cases)
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/adversarial-agent-redteam-policy.json").read_text());m=module();cases=m.generate_cases()
 if policy["exact_attack_count"]!=m.EXACT_ATTACK_COUNT or set(policy["attack_types"])!=set(m.ATTACK_TYPES):errors.append("red-team policy mismatch")
 report=m.evaluate(cases,oracle(cases,m))
 if report.release_decision!="pass" or report.overall_defense_rate!=1.0 or report.failed_attack_ids:errors.append("oracle red-team evaluation failed")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("adversarial agent red-team validation passed")
