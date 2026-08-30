from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

NODES = frozenset({"greeting","intake","clarification","device_resolution","consent","routing","outlook_diagnostics","print_scan_diagnostics","windows_network_diagnostics","evidence_fusion","planning","critic","approval","execution","rollback","verification","employee_confirmation","closure","escalation","cancelled"})
TERMINALS = frozenset({"closure","escalation","cancelled"})
EDGES = frozenset({
    ("greeting","intake"),("intake","clarification"),("intake","device_resolution"),("clarification","device_resolution"),("clarification","escalation"),("device_resolution","consent"),("device_resolution","escalation"),("consent","routing"),("consent","cancelled"),
    ("routing","outlook_diagnostics"),("routing","print_scan_diagnostics"),("routing","windows_network_diagnostics"),("routing","clarification"),("routing","escalation"),
    ("outlook_diagnostics","evidence_fusion"),("print_scan_diagnostics","evidence_fusion"),("windows_network_diagnostics","evidence_fusion"),("evidence_fusion","planning"),("evidence_fusion","clarification"),("evidence_fusion","escalation"),
    ("planning","critic"),("planning","escalation"),("critic","approval"),("critic","planning"),("critic","escalation"),("approval","execution"),("approval","cancelled"),("execution","verification"),("execution","rollback"),("execution","escalation"),("rollback","verification"),("rollback","escalation"),
    ("verification","employee_confirmation"),("verification","rollback"),("verification","outlook_diagnostics"),("verification","print_scan_diagnostics"),("verification","windows_network_diagnostics"),("verification","escalation"),("employee_confirmation","closure"),("employee_confirmation","verification"),
})
REQUIRED_GATES = ("consent","evidence_fusion","planning","critic","approval","execution","verification","employee_confirmation","closure")
REQUIRED_MODULES = frozenset({"conversation_supervisor","incident_intake","clarification","device_resolution","supervisor","domain_routing","outlook_specialist","print_scan_specialist","windows_network_specialist","evidence_fusion","remediation_planner","remediation_critic","approval_validation","execution_coordinator","outcome_verification","resolution_closure","escalation_handoff","agent_observability","regression_evaluation","adversarial_evaluation","online_quality_monitor","model_router","semantic_cache","context_compression","prompt_firewall","memory_governance","planning_governance","delegation_governance","tool_registry","mcp_dispatch"})


class IntegrationError(ValueError):pass


@dataclass(frozen=True)
class ScenarioProof:
 scenario_id:str;domain:Literal["outlook","printer","scanner","windows_network"];path:tuple[str,...];consent_granted:bool;approval_validated:bool;rollback_verified:bool;employee_confirmed:bool;final_status:Literal["resolved","escalated","cancelled"]

@dataclass(frozen=True)
class ReadinessReport:
 decision:Literal["ready","blocked"];node_count:int;edge_count:int;module_count:int;scenario_count:int;orphan_nodes:tuple[str,...];missing_modules:tuple[str,...];failed_scenarios:tuple[str,...];blockers:tuple[str,...];report_sha256:str

def _digest(value:object)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()

def validate_graph()->tuple[str,...]:
 blockers=[];reachable={"greeting"};changed=True
 while changed:
  changed=False
  for source,target in EDGES:
   if source in reachable and target not in reachable:reachable.add(target);changed=True
 orphans=sorted(NODES-reachable)
 if orphans:blockers.append("orphan_nodes")
 if any(source in TERMINALS for source,_ in EDGES):blockers.append("terminal_has_outgoing_edge")
 if not TERMINALS<=NODES:blockers.append("terminal_missing")
 return tuple(blockers)

def validate_scenario(proof:ScenarioProof)->tuple[str,...]:
 errors=[]
 if not proof.path or proof.path[0]!="greeting" or any((a,b) not in EDGES for a,b in zip(proof.path,proof.path[1:])):errors.append("invalid_graph_path")
 if proof.final_status=="resolved":
  positions={node:index for index,node in enumerate(proof.path)}
  if not all(gate in positions for gate in REQUIRED_GATES) or tuple(positions[g] for g in REQUIRED_GATES)!=tuple(sorted(positions[g] for g in REQUIRED_GATES)):errors.append("required_gate_order")
  if not (proof.consent_granted and proof.approval_validated and proof.employee_confirmed):errors.append("resolution_safety_gate")
 if "rollback" in proof.path and not proof.rollback_verified:errors.append("rollback_not_verified")
 expected_terminal={"resolved":"closure","escalated":"escalation","cancelled":"cancelled"}[proof.final_status]
 if not proof.path or proof.path[-1]!=expected_terminal:errors.append("terminal_status_mismatch")
 return tuple(errors)

def build_readiness_report(*,available_modules:frozenset[str],scenarios:tuple[ScenarioProof,...])->ReadinessReport:
 graph_blockers=list(validate_graph());reachable={"greeting"};changed=True
 while changed:
  changed=False
  for source,target in EDGES:
   if source in reachable and target not in reachable:reachable.add(target);changed=True
 orphans=tuple(sorted(NODES-reachable));missing=tuple(sorted(REQUIRED_MODULES-available_modules));failed=tuple(sorted(p.scenario_id for p in scenarios if validate_scenario(p)))
 blockers=graph_blockers+(["missing_modules"] if missing else [])+(["scenario_failures"] if failed else [])
 required_domains={"outlook","printer","scanner","windows_network"}
 if {p.domain for p in scenarios}!=required_domains:blockers.append("domain_coverage_missing")
 payload={"nodes":sorted(NODES),"edges":sorted(EDGES),"modules":sorted(available_modules),"scenarios":[p.__dict__ for p in scenarios],"orphans":orphans,"missing":missing,"failed":failed,"blockers":sorted(set(blockers))}
 return ReadinessReport("blocked" if blockers else "ready",len(NODES),len(EDGES),len(available_modules),len(scenarios),orphans,missing,failed,tuple(sorted(set(blockers))),_digest(payload))
