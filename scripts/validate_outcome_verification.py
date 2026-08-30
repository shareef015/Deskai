from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.outcome_verification")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/technical-business-verification-policy.json").read_text());config=json.loads((ROOT/"config/agents/technical-business-function-verifier.json").read_text());verify=module();limits=policy["limits"]
 if (limits["maximum_targeted_checks"],limits["maximum_regression_checks"])!=(verify.MAX_CHECKS,verify.MAX_REGRESSION_CHECKS):errors.append("verification limits mismatch")
 if config["allowed_tools"]!=["typed_read_only_diagnostics"]:errors.append("verification tools must remain read-only")
 if policy["requirements"]["technical_success_alone_cannot_resolve"] is not True:errors.append("employee confirmation gate missing")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("technical and business-function verification passed")
