from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from typing import Literal
class BrowserEvidenceDenied(ValueError):pass
@dataclass(frozen=True)
class BrowserStep:step_id:str;action:str;expected_text:str;status:Literal["passed","failed","blocked"]
@dataclass(frozen=True)
class ScreenshotEvidence:evidence_id:str;relative_path:str;sha256:str;width:int;height:int;mode:Literal["desktop","mobile"]
@dataclass(frozen=True)
class BrowserRun:run_id:str;scenario_id:str;app_build_sha256:str;synthetic_seed:str;steps:tuple[BrowserStep,...];screenshots:tuple[ScreenshotEvidence,...];console_error_count:int;result:Literal["passed","failed","blocked"];provenance_sha256:str
REQUIRED_STEPS=frozenset({"greeting","follow_up_device","follow_up_symptom","remote_permission","ui_diagnostics","repair_approval","technical_verification","employee_confirmation","dashboard","mobile_drawer","keyboard_focus","failure_decline","deterministic_reset"})
def certify(run_id:str,scenario_id:str,app_build_sha256:str,synthetic_seed:str,steps:tuple[BrowserStep,...],screenshots:tuple[ScreenshotEvidence,...],console_error_count:int)->BrowserRun:
 if not all((run_id,scenario_id,synthetic_seed)) or len(app_build_sha256)!=64:raise BrowserEvidenceDenied("run identity invalid")
 ids=[step.step_id for step in steps]
 if len(ids)!=len(set(ids)) or not REQUIRED_STEPS.issubset(ids):raise BrowserEvidenceDenied("required browser coverage missing")
 if console_error_count < 0:raise BrowserEvidenceDenied("console error count invalid")
 if console_error_count > 0 or any(step.status!="passed" for step in steps):result="failed"
 else:result="passed"
 modes={shot.mode for shot in screenshots}
 if modes!={"desktop","mobile"} or any(len(shot.sha256)!=64 or shot.width<320 or shot.height<480 or not shot.relative_path.startswith("evidence/browser/") for shot in screenshots):raise BrowserEvidenceDenied("screenshot evidence invalid")
 payload={"run":run_id,"scenario":scenario_id,"build":app_build_sha256,"seed":synthetic_seed,"steps":[step.__dict__ for step in steps],"screenshots":[shot.__dict__ for shot in screenshots],"console_errors":console_error_count,"result":result};digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest();return BrowserRun(run_id,scenario_id,app_build_sha256,synthetic_seed,steps,screenshots,console_error_count,result,digest)
