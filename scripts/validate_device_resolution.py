from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.device_resolution")
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/employee-device-resolution-policy.json").read_text());config=json.loads((ROOT/"config/agents/employee-device-resolver.json").read_text());device=module();thresholds=policy["thresholds"]
 if (thresholds["minimum_confidence"],thresholds["minimum_margin"],thresholds["maximum_disclosed_candidates"])!=(device.MIN_CONFIDENCE,device.MIN_MARGIN,device.MAX_DISCLOSED):errors.append("resolution thresholds mismatch")
 if set(policy["supported_operating_systems"])!=set(device.OS_VALUES) or set(policy["relationship_types"])!=set(device.RELATIONSHIPS):errors.append("device enums mismatch")
 if config["allowed_tools"]!=["asset_registry_lookup"]:errors.append("unexpected tool boundary")
 if policy["safety"]["diagnostics_before_confirmation"] is not False:errors.append("pre-confirmation diagnostics must be denied")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("employee device resolution validation passed")
