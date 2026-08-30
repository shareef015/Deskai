from __future__ import annotations
import importlib,json,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.frontend_quality")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/frontend-quality-policy.json").read_text());config=json.loads((ROOT/"config/agents/frontend-quality.json").read_text());css=(ROOT/"apps/web/src/app/globals.css").read_text();types=(ROOT/"apps/web/src/lib/view-models.ts").read_text();states=(ROOT/"apps/web/src/components/workspace-state.tsx").read_text();quality=module()
 for key in ("strict_view_models","unknown_fields_denied","versioned_schemas","deterministic_fingerprints","single_theme_tokens","normal_text_contrast_4_5","large_text_contrast_3","visible_focus","reduced_motion","forced_colors","responsive_targets","semantic_landmarks","live_state_announcements"):
  if policy["requirements"].get(key) is not True:errors.append(f"frontend quality control disabled: {key}")
 for marker in ("prefers-reduced-motion","forced-colors:active","min-height:44px","focus-visible","--surface-subtle"):
  if marker not in css:errors.append(f"theme/accessibility marker missing: {marker}")
 for marker in ("unknown","parseIncidentSummary","assertRecord","schemaVersion"):
  if marker not in types:errors.append(f"typed view-model marker missing: {marker}")
 if 'role="status"' not in states or 'role="alert"' not in states:errors.append("workspace states lack announcements")
 for path in (ROOT/"apps/web/src").rglob("*.tsx"):
  text=path.read_text()
  if re.search(r"\bany\b|as any|<any>",text):errors.append(f"loose frontend type: {path.relative_to(ROOT)}")
  if path.name=="page.tsx" and '<main id="main-content"' not in text:errors.append(f"main landmark missing: {path.relative_to(ROOT)}")
 if quality.contrast_ratio("#172033","#ffffff")<config["normal_text_contrast"]:errors.append("primary text contrast failed")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("Frontend type, theme and accessibility validation passed")
