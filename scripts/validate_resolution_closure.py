from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.resolution_closure")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/resolution-closure-knowledge-policy.json").read_text());config=json.loads((ROOT/"config/agents/resolution-closure-knowledge-capture.json").read_text());closure=module();limits=policy["limits"]
 if (limits["maximum_summary_characters"],limits["maximum_evidence_references"])!=(closure.MAX_SUMMARY_CHARS,closure.MAX_EVIDENCE_REFS):errors.append("closure limits mismatch")
 if config["allowed_tools"]!=[]:errors.append("closure agent must not have tools")
 if policy["knowledge_requirements"]["automatic_publication"] is not False or policy["authority"]["publish_knowledge"] is not False:errors.append("knowledge publication boundary invalid")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("resolution closure and knowledge-capture validation passed")
