from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import uuid
from dataclasses import asdict, dataclass
from typing import Literal

MAX_TOKEN_TTL_SECONDS = 300
MAX_ACTION_DEADLINE_SECONDS = 120
MAX_PLAN_ACTIONS = 4
TOKEN_NAMESPACE = uuid.UUID("b7e27834-454e-5f78-b62b-076021b7c0b8")
PROHIBITED_CAPABILITIES = frozenset({"raw_command", "powershell", "cmd", "shell", "disable_firewall", "disable_endpoint_security", "collect_credentials", "wipe_device"})


class ExecutionDenied(PermissionError):
    pass


class ExecutionConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class ApprovedPlan:
    tenant_id: str
    incident_id: str
    device_id: str
    thread_id: str
    checkpoint_id: str
    plan_id: str
    plan_provenance_sha256: str
    approval_packet_id: str
    approval_decision_fingerprint: str
    approval_status: str
    action_ids: tuple[str, ...]
    capability_ids: tuple[str, ...]


@dataclass(frozen=True)
class CapabilityToken:
    token_id: str
    tenant_id: str
    incident_id: str
    device_id: str
    plan_id: str
    plan_provenance_sha256: str
    approval_packet_id: str
    approval_decision_fingerprint: str
    action_ids: tuple[str, ...]
    capability_ids: tuple[str, ...]
    issued_at: str
    expires_at: str
    nonce: str
    signature_sha256: str


@dataclass(frozen=True)
class ActionDispatch:
    action_id: str
    capability_id: str
    parameters: dict[str, object]
    idempotency_key: str
    deadline_seconds: int
    persistent_change: bool
    pre_state: dict[str, object]
    rollback_capability_id: str | None


@dataclass(frozen=True)
class ExecutionResult:
    action_id: str
    status: Literal["succeeded", "failed", "partial", "timeout"]
    mutation_applied: bool
    rollback_supported: bool
    result_fingerprint: str


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=list).encode()


def _utc(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ExecutionDenied("timezone-aware token required")
    return parsed.astimezone(dt.timezone.utc)


def mint_capability_token(plan: ApprovedPlan, *, issued_at: dt.datetime, ttl_seconds: int, signing_key: bytes) -> CapabilityToken:
    if plan.approval_status != "approved" or len(plan.plan_provenance_sha256) != 64 or len(plan.approval_decision_fingerprint) != 64:
        raise ExecutionDenied("validated approval required")
    if issued_at.tzinfo is None or not 1 <= ttl_seconds <= MAX_TOKEN_TTL_SECONDS or len(signing_key) < 32:
        raise ExecutionDenied("invalid token security parameters")
    if not plan.action_ids or len(plan.action_ids) > MAX_PLAN_ACTIONS or len(plan.action_ids) != len(plan.capability_ids):
        raise ExecutionDenied("invalid approved action scope")
    if set(plan.capability_ids) & PROHIBITED_CAPABILITIES:
        raise ExecutionDenied("prohibited capability in approved plan")
    stable = ":".join((plan.tenant_id, plan.incident_id, plan.device_id, plan.plan_id, plan.plan_provenance_sha256, plan.approval_decision_fingerprint))
    token_id = str(uuid.uuid5(TOKEN_NAMESPACE, stable))
    nonce = hashlib.sha256((stable + ":nonce").encode()).hexdigest()[:32]
    issued = issued_at.astimezone(dt.timezone.utc); expires = issued + dt.timedelta(seconds=ttl_seconds)
    claims = {"token_id": token_id, "tenant_id": plan.tenant_id, "incident_id": plan.incident_id, "device_id": plan.device_id, "plan_id": plan.plan_id, "plan_provenance_sha256": plan.plan_provenance_sha256, "approval_packet_id": plan.approval_packet_id, "approval_decision_fingerprint": plan.approval_decision_fingerprint, "action_ids": plan.action_ids, "capability_ids": plan.capability_ids, "issued_at": issued.isoformat().replace("+00:00", "Z"), "expires_at": expires.isoformat().replace("+00:00", "Z"), "nonce": nonce}
    signature = hmac.new(signing_key, _canonical(claims), hashlib.sha256).hexdigest()
    return CapabilityToken(token_id, plan.tenant_id, plan.incident_id, plan.device_id, plan.plan_id, plan.plan_provenance_sha256, plan.approval_packet_id, plan.approval_decision_fingerprint, plan.action_ids, plan.capability_ids, claims["issued_at"], claims["expires_at"], nonce, signature)


def _verify_token(token: CapabilityToken, signing_key: bytes, now: dt.datetime) -> None:
    claims = asdict(token); signature = claims.pop("signature_sha256")
    if not hmac.compare_digest(signature, hmac.new(signing_key, _canonical(claims), hashlib.sha256).hexdigest()):
        raise ExecutionDenied("invalid capability token signature")
    if now.tzinfo is None or now.astimezone(dt.timezone.utc) > _utc(token.expires_at):
        raise ExecutionDenied("capability token expired")


def authorize_dispatch(*, token: CapabilityToken, dispatch: ActionDispatch, now: dt.datetime, signing_key: bytes, gateway_allowlist: frozenset[str], expected_plan_provenance_sha256: str, existing_dispatch_fingerprint: str | None = None) -> dict[str, object]:
    _verify_token(token, signing_key, now)
    if expected_plan_provenance_sha256 != token.plan_provenance_sha256:
        raise ExecutionDenied("plan changed after token issuance")
    pairs = set(zip(token.action_ids, token.capability_ids))
    if (dispatch.action_id, dispatch.capability_id) not in pairs or dispatch.capability_id not in gateway_allowlist or dispatch.capability_id in PROHIBITED_CAPABILITIES:
        raise ExecutionDenied("action is outside approved capability scope")
    if not dispatch.idempotency_key or not 1 <= dispatch.deadline_seconds <= MAX_ACTION_DEADLINE_SECONDS:
        raise ExecutionDenied("invalid execution bounds")
    if any(key.lower() in {"command", "script", "powershell", "shell"} for key in dispatch.parameters):
        raise ExecutionDenied("raw command parameters prohibited")
    if dispatch.persistent_change and (not dispatch.pre_state or not dispatch.rollback_capability_id):
        raise ExecutionDenied("persistent change requires pre-state and rollback")
    payload = {"token_id": token.token_id, "plan_id": token.plan_id, "action": asdict(dispatch)}
    fingerprint = hashlib.sha256(_canonical(payload)).hexdigest()
    if existing_dispatch_fingerprint is not None and existing_dispatch_fingerprint != fingerprint:
        raise ExecutionConflict("idempotency key already represents a different dispatch")
    return {"authorized_by_gateway": True, "token_id": token.token_id, "tenant_id": token.tenant_id, "incident_id": token.incident_id, "device_id": token.device_id, "plan_id": token.plan_id, "action_id": dispatch.action_id, "capability_id": dispatch.capability_id, "parameters": dispatch.parameters, "deadline_seconds": dispatch.deadline_seconds, "idempotency_key": dispatch.idempotency_key, "dispatch_fingerprint": fingerprint, "idempotent_replay": existing_dispatch_fingerprint == fingerprint}


def route_result(result: ExecutionResult) -> dict[str, object]:
    if not result.action_id or len(result.result_fingerprint) != 64:
        raise ExecutionDenied("invalid execution result")
    if result.status == "succeeded":
        phase, route = "verification", "verify_change"
    elif result.mutation_applied and result.rollback_supported:
        phase, route = "execution", "rollback"
    else:
        phase, route = "escalated", "human_recovery"
    return {"phase": phase, "execution_status": result.status, "execution_result_fingerprint": result.result_fingerprint, "execution_recovery_route": route}
