from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.domain_routing")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/conditional-domain-routing-policy.json").read_text());router=module()
 if tuple(policy["supported_domains"])!=router.SUPPORTED_DOMAINS:errors.append("supported domains mismatch")
 if policy["thresholds"]["minimum_confidence"]!=router.MIN_CONFIDENCE:errors.append("confidence mismatch")
 if policy["thresholds"]["minimum_margin"]!=router.MIN_MARGIN:errors.append("margin mismatch")
 if policy["thresholds"]["maximum_clarification_rounds"]!=router.MAX_CLARIFICATION_ROUNDS:errors.append("clarification limit mismatch")
 if policy["safety"]["classifier_grants_authority"] is not False:errors.append("classifier authority must be denied")
 if set(policy["edges"])-{"clarify","escalate"}!=set(router.SUPPORTED_DOMAINS):errors.append("explicit edge mismatch")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("conditional domain routing validation passed")
