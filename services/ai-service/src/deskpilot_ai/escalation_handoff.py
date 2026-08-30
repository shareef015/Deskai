from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from typing import Literal

MAX_HANDOFF_HOPS = 3
MAX_EVIDENCE_REFS = 20
HANDOFF_NAMESPACE = uuid.UUID("7b37ae3b-1cbd-5d62-992d-bad45a2f6a4b")
REASON_TEAM = {
    "endpoint_admin_required": "endpoint_engineering",
    "network_or_site_outage": "network_operations",
    "security_policy_change": "security_operations",
    "identity_or_certificate": "identity_messaging",
    "outlook_service_or_tenant": "identity_messaging",
    "printer_hardware_or_firmware": "workplace_hardware",
    "scanner_hardware_or_firmware": "workplace_hardware",
    "rollback_failed": "major_incident_management",
    "unsupported_domain": "service_desk_triage",
    "weak_or_contradictory_evidence": "l2_l3_support",
}
TEAM_ACK_ROLES = {
    "endpoint_engineering": "endpoint_engineer", "network_operations": "network_engineer",
    "security_operations": "security_engineer", "identity_messaging": "messaging_engineer",
    "workplace_hardware": "hardware_engineer", "major_incident_management": "incident_manager",
    "service_desk_triage": "service_desk_lead", "l2_l3_support": "l2_l3_specialist",
}
SLA_MINUTES = {"critical": 5, "high": 15, "medium": 60, "low": 240}
SECRET_PATTERN = re.compile(r"(?i)(password|token|secret|api[_-]?key)\s*[:=]\s*\S+")


class HandoffDenied(ValueError):
    pass


@dataclass(frozen=True)
class EscalationContext:
    tenant_id: str
    incident_id: str
    device_id: str
    thread_id: str
    checkpoint_id: str
    reason: str
    severity: Literal["critical", "high", "medium", "low"]
    business_impact: str
    current_owner_team: str
    visited_teams: tuple[str, ...]
    handoff_hops: int
    evidence_ids: tuple[str, ...]
    latest_provenance_sha256: str


@dataclass(frozen=True)
class HandoffPacket:
    handoff_id: str
    tenant_id: str
    incident_id: str
    device_id: str
    thread_id: str
    checkpoint_id: str
    reason: str
    severity: str
    business_impact: str
    from_team: str
    owner_team: str
    required_ack_role: str
    evidence_ids: tuple[str, ...]
    provenance_sha256: str
    created_at: str
    acknowledge_by: str
    status: Literal["pending_acknowledgement"]


@dataclass(frozen=True)
class HandoffPrincipal:
    subject: str
    tenant_id: str
    roles: frozenset[str]
    authenticated: bool
    team: str


@dataclass(frozen=True)
class HumanAction:
    handoff_id: str
    outcome: Literal["acknowledged", "resolved_by_human", "returned_for_information", "transferred"]
    summary: str
    evidence_ids: tuple[str, ...]
    target_team: str | None = None


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=list).encode()).hexdigest()


def create_handoff(context: EscalationContext, *, created_at: dt.datetime) -> HandoffPacket:
    if context.reason not in REASON_TEAM or context.handoff_hops >= MAX_HANDOFF_HOPS:
        raise HandoffDenied("unsupported escalation or maximum hops reached")
    if created_at.tzinfo is None or len(context.latest_provenance_sha256) != 64:
        raise HandoffDenied("timestamp or provenance invalid")
    if not context.evidence_ids or len(context.evidence_ids) > MAX_EVIDENCE_REFS or len(set(context.evidence_ids)) != len(context.evidence_ids):
        raise HandoffDenied("valid evidence references required")
    owner = REASON_TEAM[context.reason]
    if owner == context.current_owner_team or owner in context.visited_teams:
        raise HandoffDenied("circular escalation prohibited")
    safe_impact = SECRET_PATTERN.sub("[redacted-secret]", context.business_impact.strip())[:800]
    if not safe_impact:
        raise HandoffDenied("business impact required")
    stable = ":".join((context.tenant_id, context.incident_id, context.checkpoint_id, context.reason, owner))
    handoff_id = str(uuid.uuid5(HANDOFF_NAMESPACE, stable)); created = created_at.astimezone(dt.timezone.utc); due = created + dt.timedelta(minutes=SLA_MINUTES[context.severity])
    payload = {"scope": (context.tenant_id, context.incident_id, context.device_id), "reason": context.reason, "owner": owner, "severity": context.severity, "impact": safe_impact, "evidence": context.evidence_ids, "source": context.latest_provenance_sha256}
    return HandoffPacket(handoff_id, context.tenant_id, context.incident_id, context.device_id, context.thread_id, context.checkpoint_id, context.reason, context.severity, safe_impact, context.current_owner_team, owner, TEAM_ACK_ROLES[owner], context.evidence_ids, _digest(payload), created.isoformat().replace("+00:00", "Z"), due.isoformat().replace("+00:00", "Z"), "pending_acknowledgement")


def validate_human_action(packet: HandoffPacket, principal: HandoffPrincipal, action: HumanAction) -> dict[str, object]:
    if not principal.authenticated or principal.tenant_id != packet.tenant_id or principal.team != packet.owner_team or packet.required_ack_role not in principal.roles:
        raise HandoffDenied("authenticated owning-team acknowledgement required")
    if action.handoff_id != packet.handoff_id or not action.summary.strip():
        raise HandoffDenied("human action does not match handoff")
    if action.outcome == "resolved_by_human" and not action.evidence_ids:
        raise HandoffDenied("human resolution requires new evidence")
    if action.outcome == "transferred":
        if not action.target_team or action.target_team in {packet.from_team, packet.owner_team} or action.target_team not in TEAM_ACK_ROLES:
            raise HandoffDenied("invalid or circular transfer")
    fingerprint = _digest({"packet": packet.provenance_sha256, "actor": principal.subject, "action": action.__dict__})
    if action.outcome == "resolved_by_human": phase, route = "verification", "verify_human_change"
    elif action.outcome == "returned_for_information": phase, route = "clarification", "collect_requested_information"
    elif action.outcome == "transferred": phase, route = "escalated", "transfer_owner"
    else: phase, route = "escalated", "await_human_action"
    return {"phase": phase, "handoff_status": action.outcome, "handoff_actor_id": principal.subject, "handoff_owner_team": action.target_team or packet.owner_team, "handoff_resume_route": route, "handoff_action_fingerprint": fingerprint, "human_evidence_ids": action.evidence_ids}
