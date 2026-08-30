from __future__ import annotations
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];STATE=ROOT/"services/ai-service/src/deskpilot_ai/state.py"
def module():
 spec=importlib.util.spec_from_file_location("deskpilot_graph_state",STATE);assert spec and spec.loader;m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def validate()->list[str]:
 errors=[];policy=json.loads((ROOT/"contracts/langgraph-state-policy.json").read_text());m=module();source=STATE.read_text()
 for token in ("class GraphInput","class DeskPilotState","class GraphOutput","Annotated[","merge_messages","merge_evidence","merge_errors","merge_retry_counts","validate_state"):
  if token not in source:errors.append(f"state implementation missing {token}")
 if policy["limits"]["messages"]!=m.MAX_MESSAGES or policy["limits"]["evidence"]!=m.MAX_EVIDENCE or policy["limits"]["errors"]!=m.MAX_ERRORS:errors.append("policy and reducer limits differ")
 base=m.new_state({"tenant_id":"tenant-demo-kw","incident_id":"inc-1","thread_id":"thread-1","correlation_id":"corr-1","employee_id":"usr-001","device_id":"device-1","initial_message":"Printer offline"})
 if m.validate_state(base):errors.append("valid initial state was rejected")
 return errors
if __name__=="__main__":
 failures=validate()
 if failures:raise SystemExit("\n".join(failures))
 print("typed LangGraph state and reducer validation passed")
