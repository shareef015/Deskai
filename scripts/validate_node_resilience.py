from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.node_resilience")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/node-resilience-policy.json").read_text());res=module()
 if policy["retry"]["maximum_attempts"]!=res.MAX_ATTEMPTS:errors.append("attempt mismatch")
 if set(policy["retry"]["retryable"])!=set(res.RETRYABLE):errors.append("retryable mismatch")
 if tuple(policy["retry"]["backoff_seconds"])!=res.BACKOFF_SECONDS:errors.append("backoff mismatch")
 if policy["circuit_breaker"]["failure_threshold"]!=res.FAILURE_THRESHOLD:errors.append("circuit threshold mismatch")
 if policy["compensation"]["maximum_attempts"]!=1:errors.append("compensation must not retry")
 if policy["safety"]["authorization_failures_retryable"] is not False:errors.append("authorization retry must be denied")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("node resilience validation passed")
