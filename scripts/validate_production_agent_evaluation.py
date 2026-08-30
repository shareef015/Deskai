from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.regression_evaluation")
def oracle(expected,module):return tuple(module.Prediction(x.case_id,x.domain,x.root_cause,x.safe_remediation,x.consent_outcome,x.risk_level,x.execution_terminal_state,x.final_status,False,False,False,"a"*64,"a"*64,500,1000) for x in expected)
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/production-agent-evaluation-policy.json").read_text());data=json.loads((ROOT/"data/synthetic/regression-cases.json").read_text());ev=module()
 if policy["exact_case_count"]!=ev.EXACT_CASE_COUNT or policy["release_thresholds"]!=ev.RELEASE_THRESHOLDS:errors.append("evaluation policy mismatch")
 expected,digest=ev.load_expected(data);report=ev.evaluate(expected,oracle(expected,ev),digest)
 if report.release_decision!="pass" or len(report.slice_metrics)!=8 or report.failed_case_ids:errors.append("oracle corpus evaluation failed")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("production agent evaluation and regression validation passed")
