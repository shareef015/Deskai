from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.semantic_cache")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/tenant-safe-semantic-cache-policy.json").read_text());m=module()
 if policy["maximum_ttl_seconds"]!=m.MAX_TTL_SECONDS or policy["similarity_thresholds"]!={"response":m.MIN_RESPONSE_SIMILARITY,"retrieval":m.MIN_RETRIEVAL_SIMILARITY}:errors.append("semantic cache policy mismatch")
 if policy["requirements"]["cross_tenant_reuse"] is not False or policy["requirements"]["high_risk_reasoning_cache"] is not False:errors.append("semantic cache safety boundary invalid")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("tenant-safe semantic cache validation passed")
