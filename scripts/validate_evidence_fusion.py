from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.evidence_fusion")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/evidence-fusion-policy.json").read_text());config=json.loads((ROOT/"config/agents/evidence-fusion-root-cause.json").read_text());fusion=module();limits=policy["limits"]
 if (limits["maximum_evidence"],limits["maximum_candidates"],limits["minimum_root_cause_score"],limits["minimum_independent_source_types"])!=(fusion.MAX_EVIDENCE,fusion.MAX_CANDIDATES,fusion.MIN_ROOT_CAUSE_SCORE,fusion.MIN_INDEPENDENT_SOURCE_TYPES):errors.append("evidence-fusion limits mismatch")
 if config["allowed_tools"]!=[]:errors.append("fusion agent must not have tools")
 if policy["requirements"]["rag_cannot_be_sole_authority"] is not True or policy["requirements"]["contradictions_preserved"] is not True:errors.append("grounding requirements missing")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("evidence-fusion and root-cause validation passed")
