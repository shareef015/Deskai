from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

SourceType = Literal["specialist", "telemetry", "rag", "employee", "inventory"]
Decision = Literal["root_cause_ready", "insufficient_evidence", "contradictory_evidence", "escalate"]
MAX_EVIDENCE = 40
MAX_CANDIDATES = 6
MIN_ROOT_CAUSE_SCORE = 0.78
MIN_INDEPENDENT_SOURCE_TYPES = 2
SOURCE_WEIGHT = {"telemetry": 1.0, "specialist": 0.9, "inventory": 0.8, "employee": 0.6, "rag": 0.5}


class EvidenceFusionError(ValueError):
    pass


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    tenant_id: str
    incident_id: str
    source_type: SourceType
    source_id: str
    observation_key: str
    value: str
    reliability: float
    freshness_seconds: int


@dataclass(frozen=True)
class Candidate:
    cause: str
    supporting_evidence_ids: tuple[str, ...]
    contradicting_evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class FusionResult:
    decision: Decision
    selected_root_cause: str | None
    ranked_hypotheses: tuple[dict[str, object], ...]
    contradiction_keys: tuple[str, ...]
    reason: str
    provenance_sha256: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _validate_evidence(items: tuple[Evidence, ...], tenant_id: str, incident_id: str) -> dict[str, Evidence]:
    if not items or len(items) > MAX_EVIDENCE:
        raise EvidenceFusionError("invalid evidence count")
    by_id: dict[str, Evidence] = {}
    for item in items:
        if item.tenant_id != tenant_id or item.incident_id != incident_id:
            raise EvidenceFusionError("cross-scope evidence")
        if not item.evidence_id or item.evidence_id in by_id or not item.source_id or not item.observation_key:
            raise EvidenceFusionError("invalid or duplicate evidence")
        if isinstance(item.reliability, bool) or not 0 <= item.reliability <= 1 or item.freshness_seconds < 0:
            raise EvidenceFusionError("invalid evidence quality")
        by_id[item.evidence_id] = item
    return by_id


def _contradictions(items: tuple[Evidence, ...]) -> tuple[str, ...]:
    values: dict[str, set[str]] = {}
    for item in items:
        if item.reliability >= 0.7:
            values.setdefault(item.observation_key, set()).add(item.value)
    return tuple(sorted(key for key, observed in values.items() if len(observed) > 1))


def fuse_evidence(tenant_id: str, incident_id: str, evidence: tuple[Evidence, ...], candidates: tuple[Candidate, ...]) -> FusionResult:
    by_id = _validate_evidence(evidence, tenant_id, incident_id)
    if not candidates or len(candidates) > MAX_CANDIDATES or len({c.cause for c in candidates}) != len(candidates):
        raise EvidenceFusionError("invalid candidates")
    contradictions = _contradictions(evidence)
    ranked: list[dict[str, object]] = []
    for candidate in candidates:
        support_ids = set(candidate.supporting_evidence_ids)
        oppose_ids = set(candidate.contradicting_evidence_ids)
        if not support_ids or support_ids & oppose_ids or not (support_ids | oppose_ids) <= by_id.keys():
            raise EvidenceFusionError("candidate references invalid evidence")
        support = [by_id[item_id] for item_id in sorted(support_ids)]
        oppose = [by_id[item_id] for item_id in sorted(oppose_ids)]
        source_types = {item.source_type for item in support}
        independent_sources = {(item.source_type, item.source_id) for item in support}
        weighted_support = sum(item.reliability * SOURCE_WEIGHT[item.source_type] for item in support)
        weighted_oppose = sum(item.reliability * SOURCE_WEIGHT[item.source_type] for item in oppose)
        score = round(weighted_support / max(weighted_support + weighted_oppose, 1.0), 4)
        eligible = len(source_types) >= MIN_INDEPENDENT_SOURCE_TYPES and len(independent_sources) >= 2 and source_types != {"rag"}
        ranked.append({"cause": candidate.cause, "score": score, "eligible": eligible, "supporting_evidence_ids": tuple(sorted(support_ids)), "contradicting_evidence_ids": tuple(sorted(oppose_ids)), "source_types": tuple(sorted(source_types))})
    ranked.sort(key=lambda item: (-float(item["score"]), str(item["cause"])))
    top = ranked[0]
    close_competitor = len(ranked) > 1 and bool(ranked[1]["eligible"]) and float(ranked[1]["score"]) >= MIN_ROOT_CAUSE_SCORE and float(top["score"]) - float(ranked[1]["score"]) < 0.08
    if contradictions or close_competitor:
        decision, selected, reason = "contradictory_evidence", None, "material_contradiction_preserved"
    elif bool(top["eligible"]) and float(top["score"]) >= MIN_ROOT_CAUSE_SCORE:
        decision, selected, reason = "root_cause_ready", str(top["cause"]), "grounded_threshold_met"
    else:
        decision, selected, reason = "insufficient_evidence", None, "independence_or_confidence_below_threshold"
    payload = {"tenant_id": tenant_id, "incident_id": incident_id, "ranked": ranked, "contradictions": contradictions, "decision": decision}
    return FusionResult(decision, selected, tuple(ranked), contradictions, reason, _digest(payload))


def supervisor_handoff(result: FusionResult) -> dict[str, object]:
    phase = "remediation_planning" if result.decision == "root_cause_ready" else "clarification" if result.decision == "insufficient_evidence" else "escalated"
    return {"phase": phase, "selected_root_cause": result.selected_root_cause, "evidence_fusion_status": result.decision, "ranked_hypotheses": result.ranked_hypotheses, "contradiction_keys": result.contradiction_keys, "evidence_fusion_provenance_sha256": result.provenance_sha256}
