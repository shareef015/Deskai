from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/api/src"))
def module():return importlib.import_module("deskpilot_api.operational_insights")
def validate():
 errors=[];policy=json.loads((ROOT/"contracts/operational-insights-policy.json").read_text());config=json.loads((ROOT/"config/agents/operational-insights.json").read_text());ui=(ROOT/"apps/web/src/app/insights-dashboard/page.tsx").read_text();shell=(ROOT/"apps/web/src/components/app-shell.tsx").read_text();module()
 for key in ("tenant_scoped","live_synthetic_isolated","role_gated","bounded_window","typed_units","deterministic_series","accessible_chart_summaries","no_color_only_encoding","zero_baseline_for_counts","freshness_visible"):
  if policy["requirements"].get(key) is not True:errors.append(f"insight control disabled: {key}")
 for marker in ("SLA aging","Incident volume and risk","Recovery trend","RAG quality","Agent latency","aria-label","View data table","Updated 1 minute ago"):
  if marker not in ui:errors.append(f"dashboard marker missing: {marker}")
 if "/insights-dashboard" not in shell:errors.append("insights dashboard has no navigation owner")
 if config.get("synthetic_live_mix_allowed") is not False:errors.append("live and synthetic metrics can mix")
 return errors
if __name__=="__main__":
 errors=validate()
 if errors:raise SystemExit("\n".join(errors))
 print("Operational insights validation passed")
