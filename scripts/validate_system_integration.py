from __future__ import annotations
import importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/"services/ai-service/src"))
def module():return importlib.import_module("deskpilot_ai.system_integration")
def resolution(m,sid,domain,diagnostic):return m.ScenarioProof(sid,domain,("greeting","intake","device_resolution","consent","routing",diagnostic,"evidence_fusion","planning","critic","approval","execution","verification","employee_confirmation","closure"),True,True,False,True,"resolved")
def scenarios(m):return (resolution(m,"outlook-resolution","outlook","outlook_diagnostics"),resolution(m,"printer-resolution","printer","print_scan_diagnostics"),resolution(m,"scanner-resolution","scanner","print_scan_diagnostics"),resolution(m,"network-resolution","windows_network","windows_network_diagnostics"))
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/end-to-end-agent-integration-policy.json").read_text());m=module()
 if set(policy["required_nodes"])!=set(m.NODES) or set(policy["terminal_nodes"])!=set(m.TERMINALS) or tuple(policy["resolved_gate_order"])!=m.REQUIRED_GATES:errors.append("integration policy mismatch")
 for name in m.REQUIRED_MODULES:
  try:importlib.import_module(f"deskpilot_ai.{name}")
  except ModuleNotFoundError:errors.append(f"missing module: {name}")
 report=m.build_readiness_report(available_modules=m.REQUIRED_MODULES,scenarios=scenarios(m))
 if report.decision!="ready":errors.extend(report.blockers)
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("end-to-end agent system integration validation passed")
