from __future__ import annotations

import datetime as dt
import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from typing import Literal

Decision = Literal["approved", "rejected"]
MAX_APPROVAL_TTL_MINUTES = 15
PACKET_NAMESPACE = uuid.UUID("0fd4adf4-2c88-55c6-8e78-98eeb54512a4")
RISK_ROLES = {
    "low": frozenset({"service_desk_lead", "endpoint_administrator"}),
    "medium": frozenset({"endpoint_administrator", "network_administrator", "messaging_administrator"}),
    "high": frozenset({"security_administrator", "identity_administrator", "network_administrator", "messaging_administrator"}),
}


class ApprovalDenied(PermissionError):
    pass


class ApprovalConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class ApprovalPacket:
    packet_id: str
    version: str
    tenant_id: str
    incident_id: str
    device_id: str
    thread_id: str
    checkpoint_id: str
    plan_id: str
    plan_provenance_sha256: str
    critic_provenance_sha256: str
    risk: Literal["low", "medium", "high"]
    action_ids: tuple[str, ...]
    capability_ids: tuple[str, ...]
    requester_id: str
    plan_author_id: str
    required_approver_roles: tuple[str, ...]
    issued_at: str
    expires_at: str
    status: Literal["pending", "decided", "revoked"] = "pending"
    revoked_at: str | None = None


@dataclass(frozen=True)
class ApprovalPrincipal:
    subject: str
    tenant_id: str
    roles: frozenset[str]
    authenticated: bool
    is_ai: bool = False


@dataclass(frozen=True)
class ApprovalDecision:
    packet_id: str
    version: str
    plan_id: str
    plan_provenance_sha256: str
    decision: Decision
    reason: str


def _utc(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ApprovalDenied("timezone-aware timestamp required")
    return parsed.astimezone(dt.timezone.utc)


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=list).encode()).hexdigest()


def create_packet(*, tenant_id: str, incident_id: str, device_id: str, thread_id: str, checkpoint_id: str, plan_id: str, plan_provenance_sha256: str, critic_status: str, critic_provenance_sha256: str, risk: Literal["low", "medium", "high"], action_ids: tuple[str, ...], capability_ids: tuple[str, ...], requester_id: str, plan_author_id: str, required_approver_roles: tuple[str, ...], issued_at: dt.datetime, ttl_minutes: int) -> ApprovalPacket:
    if critic_status != "pass":
        raise ApprovalDenied("independent critic pass required")
    if issued_at.tzinfo is None or not 1 <= ttl_minutes <= MAX_APPROVAL_TTL_MINUTES:
        raise ApprovalDenied("invalid approval lifetime")
    if len(plan_provenance_sha256) != 64 or len(critic_provenance_sha256) != 64 or not action_ids or len(action_ids) != len(capability_ids):
        raise ApprovalDenied("approval packet contract incomplete")
    if requester_id == plan_author_id:
        raise ApprovalDenied("plan author cannot request approval")
    qualified = RISK_ROLES[risk]
    roles = tuple(sorted(set(required_approver_roles) & qualified))
    if not roles:
        raise ApprovalDenied("qualified approver role required")
    stable = ":".join((tenant_id, incident_id, device_id, thread_id, checkpoint_id, plan_id, plan_provenance_sha256))
    packet_id = str(uuid.uuid5(PACKET_NAMESPACE, stable))
    issued = issued_at.astimezone(dt.timezone.utc)
    expires = issued + dt.timedelta(minutes=ttl_minutes)
    return ApprovalPacket(packet_id, "1.0.0", tenant_id, incident_id, device_id, thread_id, checkpoint_id, plan_id, plan_provenance_sha256, critic_provenance_sha256, risk, action_ids, capability_ids, requester_id, plan_author_id, roles, issued.isoformat().replace("+00:00", "Z"), expires.isoformat().replace("+00:00", "Z"))


def validate_decision(*, packet: ApprovalPacket, principal: ApprovalPrincipal, submission: ApprovalDecision, now: dt.datetime, expected_plan_provenance_sha256: str, existing_decision_fingerprint: str | None = None) -> dict[str, object]:
    if not principal.authenticated or principal.is_ai or "ai_service" in principal.roles or "auditor" in principal.roles:
        raise ApprovalDenied("authenticated human approver required")
    if packet.status != "pending" or packet.revoked_at is not None:
        raise ApprovalDenied("approval packet is no longer pending")
    if now.tzinfo is None or now.astimezone(dt.timezone.utc) > _utc(packet.expires_at):
        raise ApprovalDenied("approval packet expired")
    if principal.tenant_id != packet.tenant_id or principal.subject in {packet.requester_id, packet.plan_author_id}:
        raise ApprovalDenied("approval scope or segregation of duties mismatch")
    if not principal.roles.intersection(packet.required_approver_roles) or not principal.roles.intersection(RISK_ROLES[packet.risk]):
        raise ApprovalDenied("approver lacks risk-qualified authority")
    if submission.packet_id != packet.packet_id or submission.version != packet.version or submission.plan_id != packet.plan_id:
        raise ApprovalDenied("decision does not match packet")
    if submission.plan_provenance_sha256 != packet.plan_provenance_sha256 or expected_plan_provenance_sha256 != packet.plan_provenance_sha256:
        raise ApprovalDenied("plan changed after approval request")
    if submission.decision not in {"approved", "rejected"} or not submission.reason.strip():
        raise ApprovalDenied("explicit decision and reason required")
    fingerprint = _digest({"packet": asdict(packet), "actor": principal.subject, "decision": asdict(submission)})
    if existing_decision_fingerprint is not None and existing_decision_fingerprint != fingerprint:
        raise ApprovalConflict("approval already has a different decision")
    return {"validated_by_server": True, "packet_id": packet.packet_id, "plan_id": packet.plan_id, "plan_provenance_sha256": packet.plan_provenance_sha256, "decision": submission.decision, "reason": submission.reason, "actor_id": principal.subject, "decision_fingerprint": fingerprint, "idempotent_replay": existing_decision_fingerprint == fingerprint, "decided_at": now.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")}


def supervisor_handoff(validated: dict[str, object]) -> dict[str, object]:
    if validated.get("validated_by_server") is not True:
        raise ApprovalDenied("unvalidated approval decision")
    phase = "execution" if validated["decision"] == "approved" else "cancelled"
    return {"phase": phase, "approval_packet_id": validated["packet_id"], "approval_status": validated["decision"], "approval_actor_id": validated["actor_id"], "approval_decision_fingerprint": validated["decision_fingerprint"]}
