from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.model_router")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/quality-aware-model-routing-policy.json").read_text());m=module()
 if policy["limits"]["maximum_fallbacks"]!=m.MAX_FALLBACKS or policy["minimum_evaluation_score"]!=m.MIN_EVALUATION_SCORE:errors.append("model-router policy mismatch")
 if policy["requirements"]["silent_substitution"] is not False:errors.append("silent substitution must be prohibited")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("quality-aware model routing validation passed")
