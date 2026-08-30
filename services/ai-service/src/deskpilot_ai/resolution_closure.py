from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Literal

MAX_SUMMARY_CHARS = 1600
MAX_EVIDENCE_REFS = 20
SECRET_PATTERN = re.compile(r"(?i)(password|passwd|token|secret|api[_-]?key|private[_-]?key)\s*[:=]\s*\S+")
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


class ClosureDenied(ValueError):
    pass


@dataclass(frozen=True)
class ClosureContext:
    tenant_id: str
    incident_id: str
    device_id: str
    domain: Literal["outlook", "printer", "scanner", "windows", "network"]
    root_cause: str
    root_cause_provenance_sha256: str
    plan_id: str
    plan_provenance_sha256: str
    approval_packet_id: str
    approval_decision_fingerprint: str
    execution_result_fingerprint: str
    verification_status: str
    verification_provenance_sha256: str
    employee_confirmation_actor_id: str
    employee_confirmation_status: str
    evidence_ids: tuple[str, ...]
    recurrence_detected: bool = False


@dataclass(frozen=True)
class KnowledgeCandidate:
    candidate_id: str
    domain: str
    title: str
    problem_pattern: str
    grounded_resolution: str
    evidence_ids: tuple[str, ...]
    status: Literal["pending_human_review"]
    content_redacted: bool


@dataclass(frozen=True)
class ClosureRecord:
    outcome: Literal["closed", "reopened", "escalated"]
    resolution_summary: str
    evidence_ids: tuple[str, ...]
    audit_provenance: dict[str, str]
    knowledge_candidate: KnowledgeCandidate | None
    reason: str
    closure_provenance_sha256: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=list).encode()).hexdigest()


def _redact(value: str) -> str:
    return EMAIL_PATTERN.sub("[redacted-email]", SECRET_PATTERN.sub("[redacted-secret]", value))


def close_incident(context: ClosureContext, *, resolution_text: str, knowledge_title: str, problem_pattern: str) -> ClosureRecord:
    required_hashes = (context.root_cause_provenance_sha256, context.plan_provenance_sha256, context.approval_decision_fingerprint, context.execution_result_fingerprint, context.verification_provenance_sha256)
    if any(len(value) != 64 for value in required_hashes):
        raise ClosureDenied("complete provenance chain required")
    if not context.evidence_ids or len(context.evidence_ids) > MAX_EVIDENCE_REFS or len(set(context.evidence_ids)) != len(context.evidence_ids):
        raise ClosureDenied("valid evidence references required")
    if context.recurrence_detected:
        payload = {"incident": context.incident_id, "outcome": "reopened", "verification": context.verification_provenance_sha256}
        return ClosureRecord("reopened", "Previously verified issue has recurred; a new diagnostic cycle is required.", context.evidence_ids, {}, None, "recurrence_detected", _digest(payload))
    if context.verification_status != "verified" or context.employee_confirmation_status != "confirmed" or not context.employee_confirmation_actor_id:
        raise ClosureDenied("technical verification and employee confirmation required")
    if not all((context.root_cause, context.plan_id, context.approval_packet_id)):
        raise ClosureDenied("closure prerequisites incomplete")
    safe_resolution = _redact(resolution_text.strip())[:MAX_SUMMARY_CHARS]
    safe_problem = _redact(problem_pattern.strip())[:MAX_SUMMARY_CHARS]
    safe_title = _redact(knowledge_title.strip())[:160]
    if not safe_resolution or not safe_problem or not safe_title:
        raise ClosureDenied("resolution summary incomplete")
    audit = {"root_cause": context.root_cause_provenance_sha256, "plan": context.plan_provenance_sha256, "approval": context.approval_decision_fingerprint, "execution": context.execution_result_fingerprint, "verification": context.verification_provenance_sha256}
    candidate_payload = {"domain": context.domain, "title": safe_title, "problem": safe_problem, "resolution": safe_resolution, "evidence": context.evidence_ids}
    candidate = KnowledgeCandidate("knc-" + _digest(candidate_payload)[:20], context.domain, safe_title, safe_problem, safe_resolution, context.evidence_ids, "pending_human_review", True)
    summary = f"Root cause: {context.root_cause}. Verified resolution: {safe_resolution}"
    payload = {"scope": (context.tenant_id, context.incident_id, context.device_id), "summary": summary, "audit": audit, "candidate_id": candidate.candidate_id}
    return ClosureRecord("closed", summary, context.evidence_ids, audit, candidate, "closure_prerequisites_met", _digest(payload))


def supervisor_handoff(record: ClosureRecord) -> dict[str, object]:
    phase = "resolved" if record.outcome == "closed" else "diagnosis" if record.outcome == "reopened" else "escalated"
    return {"phase": phase, "final_status": "resolved" if record.outcome == "closed" else None, "closure_status": record.outcome, "resolution_summary": record.resolution_summary, "closure_provenance_sha256": record.closure_provenance_sha256, "knowledge_candidate_id": record.knowledge_candidate.candidate_id if record.knowledge_candidate else None}
