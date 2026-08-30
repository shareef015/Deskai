from __future__ import annotations
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/guided-demo-policy.json").read_text());path=ROOT/"data/synthetic/demo-packs.json";data=json.loads(path.read_text())
 spec=importlib.util.spec_from_file_location("generator",ROOT/"data/synthetic/generate_demo_packs.py");assert spec and spec.loader;generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)
 if path.read_bytes()!=generator.canonical_bytes():errors.append("demo packs are not deterministic")
 packs=data.get("packs",[])
 if len(packs)<policy["minimum_packs"] or data.get("pack_count")!=len(packs):errors.append("demo pack count is invalid")
 if len({p.get("pack_id") for p in packs})!=len(packs) or len({p.get("slug") for p in packs})!=len(packs):errors.append("demo pack identifiers are not unique")
 required={"outlook_resolution","printer_resolution","scanner_resolution","network_resolution","consent_declined","approval_rejected","rollback_success","rollback_failure"}
 if required!={p.get("slug") for p in packs}:errors.append("curated demonstration coverage is incomplete")
 if any(not p.get("synthetic_only") or len(p.get("steps",[]))>policy["maximum_steps_per_pack"] or len(p.get("steps",[]))<7 for p in packs):errors.append("demo safety or step bounds are invalid")
 service=(ROOT/"services/api/src/deskpilot_api/synthetic/guided_demo.py").read_text();routes=(ROOT/"services/api/src/deskpilot_api/routes/guided_demo.py").read_text();ui=(ROOT/"apps/web/src/app/guided-demo/page.tsx").read_text()
 for token in ("RESET GUIDED DEMO","is_ai","unknown curated demo pack","synthetic_only"):
  if token not in service:errors.append(f"guided service missing {token}")
 if "Synthetic demo only" not in ui or "No production endpoint" not in ui or "window.prompt" in ui or "alert(" in ui:errors.append("guided UI safety contract is invalid")
 if "/api/v1/guided-demo" not in routes or "require_principal" not in routes:errors.append("guided API route is not authenticated")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("recruiter demo packs and guided mode validation passed")
