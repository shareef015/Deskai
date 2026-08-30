from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.knowledge_publishing")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/knowledge-publishing-policy.json").read_text());config=json.loads((ROOT/"config/agents/knowledge-publishing.json").read_text());ui=(ROOT/"apps/web/src/app/knowledge-review/page.tsx").read_text();module()
 for key in ("de_identification","quality_gates","duplicate_block","independent_technical_approval","immutable_versions","index_generation_fingerprint","retirement"):
  if policy["requirements"].get(key) is not True:errors.append(f"knowledge control disabled: {key}")
 if config.get("automatic_publication") is not False:errors.append("automatic publication enabled")
 for marker in ("de-identification passed","Quality and duplicate review","Independent technical review","tenant RAG index refresh","Retire published guidance"):
  if marker not in ui:errors.append(f"knowledge UI marker missing: {marker}")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("knowledge publishing validation passed")
