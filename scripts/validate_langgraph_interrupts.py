from __future__ import annotations
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];MODULE=ROOT/"services/ai-service/src/deskpilot_ai/interrupts.py";NODES=ROOT/"services/ai-service/src/deskpilot_ai/interrupt_nodes.py"
def module():
 spec=importlib.util.spec_from_file_location("deskpilot_interrupts",MODULE);assert spec and spec.loader;m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/langgraph-interrupt-policy.json").read_text());source=MODULE.read_text();nodes=NODES.read_text();m=module()
 for token in ("validate_resume","decision_fingerprint","existing_fingerprint","ResumeDenied","DecisionConflict","Command(resume=","ainvoke"):
  if token not in source:errors.append(f"resume gate missing {token}")
 for token in ("diagnostic_consent_interrupt_node","remediation_approval_interrupt_node","employee_confirmation_interrupt_node","interrupt(","validated_by_server"):
  if token not in nodes:errors.append(f"interrupt nodes missing {token}")
 if set(policy["kinds"])!=set(m.DECISIONS) or policy["maximum_ttl_minutes"]!=m.MAX_TTL:errors.append("interrupt policy and implementation differ")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("LangGraph human interrupt and authenticated resume validation passed")
