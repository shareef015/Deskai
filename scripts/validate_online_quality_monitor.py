from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.online_quality_monitor")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/online-agent-quality-monitoring-policy.json").read_text());config=json.loads((ROOT/"config/agents/online-agent-quality-monitor.json").read_text());m=module();limits=policy["limits"]
 if (limits["minimum_window_size"],limits["maximum_window_size"])!=(m.MIN_WINDOW_SIZE,m.MAX_WINDOW_SIZE):errors.append("monitor window limits mismatch")
 if set(policy["zero_tolerance_metrics"])!=set(m.CRITICAL_ZERO_TOLERANCE) or policy["lower_bounds"]!=m.LOWER_BOUND_METRICS or policy["upper_bounds"]!=m.UPPER_BOUND_METRICS:errors.append("monitor thresholds mismatch")
 if policy["requirements"]["raw_content_monitoring"] is not False or policy["requirements"]["automatic_policy_promotion"] is not False:errors.append("monitor privacy or authority boundary invalid")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("online agent quality drift and safety monitoring validation passed")
