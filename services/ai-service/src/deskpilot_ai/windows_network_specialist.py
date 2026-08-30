from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

Domain = Literal["windows", "network"]
MAX_DIAGNOSTICS = 12
MAX_HYPOTHESES = 5
MAX_RAG_QUERIES = 2
MAX_REMEDIATIONS = 3
MIN_ROOT_CAUSE_CONFIDENCE = 0.75
TOOLS = frozenset({
    "windows_inventory", "service_status", "process_snapshot", "bounded_event_log",
    "resource_snapshot", "windows_update_state", "adapter_state", "ip_configuration",
    "route_table", "dns_resolution", "proxy_state", "vpn_state", "target_port_test",
    "firewall_policy_state",
})
SECURITY_BOUNDARIES = frozenset({
    "disable_firewall", "add_firewall_exception", "disable_endpoint_security",
    "export_private_key", "collect_wifi_key", "collect_vpn_secret",
    "change_enterprise_policy",
})


class WindowsNetworkError(ValueError):
    pass


@dataclass(frozen=True)
class WindowsNetworkContext:
    tenant_id: str
    incident_id: str
    device_id: str
    consent_status: str
    domain: Domain
    windows_version: str
    windows_build: str
    connection_type: str | None
    target_business_function: str
    vpn_expected: bool


@dataclass(frozen=True)
class DiagnosticPlan:
    domain: Domain
    steps: tuple[str, ...]
    tools: tuple[str, ...]
    rag_queries: tuple[dict[str, object], ...]
    outcome: Literal["diagnose", "clarify", "escalate"]
    reason: str
    provenance_sha256: str


@dataclass(frozen=True)
class Hypothesis:
    name: str
    confidence: float
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class RemediationProposal:
    action: str
    risk: Literal["low", "medium", "high"]
    required_approver: str
    pre_state_required: bool
    rollback: str | None
    verification: tuple[str, ...]


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def plan_diagnostics(context: WindowsNetworkContext) -> DiagnosticPlan:
    if context.consent_status != "granted":
        raise WindowsNetworkError("diagnostic consent required")
    if context.domain not in {"windows", "network"}:
        raise WindowsNetworkError("unsupported domain")
    if context.domain == "network" and not context.connection_type:
        return DiagnosticPlan(context.domain, (), (), (), "clarify", "connection_type_required", _digest(context.__dict__))
    common = ["inspect_windows_build", "inspect_service_state", "inspect_process_snapshot", "collect_bounded_event_window"]
    if context.domain == "windows":
        steps = common + ["inspect_resource_pressure", "inspect_windows_update_state"]
        selected = {"windows_inventory", "service_status", "process_snapshot", "bounded_event_log", "resource_snapshot", "windows_update_state"}
    else:
        steps = common + ["inspect_adapter", "inspect_ip_dhcp_gateway", "inspect_routes", "test_dns", "inspect_proxy", "inspect_vpn", "inspect_firewall_policy_read_only", "test_target_port"]
        selected = TOOLS
    filters = {"tenant_id": context.tenant_id, "domain": context.domain, "windows_version": context.windows_version, "windows_build": context.windows_build, "connection_type": context.connection_type or "not_applicable", "vpn_expected": context.vpn_expected, "permission": "employee_support"}
    query = ({"query": f"Windows {context.domain} diagnosis for {context.target_business_function}", "filters": filters},)
    payload = {"steps": steps[:MAX_DIAGNOSTICS], "tools": sorted(selected), "query": query}
    return DiagnosticPlan(context.domain, tuple(steps[:MAX_DIAGNOSTICS]), tuple(sorted(selected)), query, "diagnose", "layered_read_only_plan", _digest(payload))


def validate_hypotheses(items: tuple[Hypothesis, ...]) -> str:
    if not items or len(items) > MAX_HYPOTHESES:
        raise WindowsNetworkError("invalid hypotheses")
    for item in items:
        if not item.name or isinstance(item.confidence, bool) or not 0 <= item.confidence <= 1 or not item.evidence_ids:
            raise WindowsNetworkError("ungrounded hypothesis")
    ordered = sorted(items, key=lambda item: (-item.confidence, item.name))
    if len(ordered) > 1 and ordered[1].confidence >= MIN_ROOT_CAUSE_CONFIDENCE and ordered[0].confidence - ordered[1].confidence < 0.1:
        return "contradictory_evidence"
    return "root_cause_ready" if ordered[0].confidence >= MIN_ROOT_CAUSE_CONFIDENCE else "insufficient_evidence"


def validate_remediation(proposal: RemediationProposal) -> None:
    if proposal.action in SECURITY_BOUNDARIES:
        raise WindowsNetworkError("security or enterprise policy bypass prohibited")
    required = {"technical_state_verified", "target_business_function_works", "employee_confirms"}
    if not required <= set(proposal.verification):
        raise WindowsNetworkError("end-to-end verification incomplete")
    if proposal.risk in {"medium", "high"} and (not proposal.pre_state_required or not proposal.rollback):
        raise WindowsNetworkError("persistent change requires pre-state and rollback")
    if proposal.risk == "high" and proposal.required_approver not in {"endpoint_administrator", "network_administrator", "security_administrator", "identity_administrator"}:
        raise WindowsNetworkError("high-risk proposal requires qualified administrator")


def specialist_handoff(plan: DiagnosticPlan, hypotheses: tuple[Hypothesis, ...], proposals: tuple[RemediationProposal, ...]) -> dict[str, object]:
    if len(proposals) > MAX_REMEDIATIONS:
        raise WindowsNetworkError("too many proposals")
    status = validate_hypotheses(hypotheses)
    for proposal in proposals:
        validate_remediation(proposal)
    phase = "clarification" if status == "insufficient_evidence" else "evidence_fusion"
    return {"phase": phase, "windows_network_domain": plan.domain, "windows_network_plan_sha256": plan.provenance_sha256, "windows_network_hypothesis_status": status, "hypotheses": tuple(item.name for item in hypotheses), "remediation_proposals": tuple(item.__dict__ for item in proposals)}
