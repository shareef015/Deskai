from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.context_compression")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/context-compression-policy.json").read_text());m=module();limits=policy["limits"]
 if (limits["maximum_context_tokens"],limits["target_compressed_tokens"],limits["maximum_summary_items"])!=(m.MAX_CONTEXT_TOKENS,m.TARGET_COMPRESSED_TOKENS,m.MAX_SUMMARY_ITEMS):errors.append("compression limits mismatch")
 if set(policy["pinned_keys"])!=set(m.PINNED_KEYS):errors.append("pinned context mismatch")
 if policy["requirements"]["cross_scope_merge"] is not False or policy["requirements"]["summary_may_override_pinned_state"] is not False:errors.append("compression safety boundary invalid")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("production context compression validation passed")
