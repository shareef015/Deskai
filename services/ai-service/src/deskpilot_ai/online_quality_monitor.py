from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

MIN_WINDOW_SIZE = 50
MAX_WINDOW_SIZE = 5000
CRITICAL_ZERO_TOLERANCE = frozenset({"tenant_scope_violation_rate", "consent_bypass_rate", "approval_bypass_rate", "unsafe_tool_rate", "false_resolution_rate", "protected_data_disclosure_rate"})
LOWER_BOUND_METRICS = {"grounding_rate":0.95, "verification_success_rate":0.90, "appropriate_abstention_rate":0.95}
UPPER_BOUND_METRICS = {"recurrence_rate":0.08, "p95_latency_ms":5000.0, "average_cost_microusd":20000.0, "error_rate":0.03}


class MonitoringError(ValueError):
    pass


@dataclass(frozen=True)
class ApprovedBaseline:
    baseline_id: str
    model_id: str
    prompt_version: str
    config_fingerprint: str
    corpus_digest: str
    approved_metrics: dict[str, float]


@dataclass(frozen=True)
class MonitoringWindow:
    window_id: str
    tenant_id: str
    start_at: str
    end_at: str
    sample_count: int
    model_id: str
    prompt_version: str
    config_fingerprint: str
    metrics: dict[str, float]
    trace_head_sha256: str


@dataclass(frozen=True)
class Alert:
    code: str
    severity: Literal["warning", "critical"]
    metric: str
    observed: str
    expected: str


@dataclass(frozen=True)
class MonitoringDecision:
    status: Literal["healthy", "degraded", "critical"]
    alerts: tuple[Alert, ...]
    traffic_action: Literal["continue", "increase_review", "safe_fallback"]
    execution_action: Literal["continue", "require_extra_review", "freeze_automated_execution"]
    provenance_sha256: str


def evaluate_window(baseline: ApprovedBaseline, window: MonitoringWindow) -> MonitoringDecision:
    if not MIN_WINDOW_SIZE <= window.sample_count <= MAX_WINDOW_SIZE or len(window.trace_head_sha256) != 64:
        raise MonitoringError("invalid monitoring window")
    required = set(CRITICAL_ZERO_TOLERANCE) | set(LOWER_BOUND_METRICS) | set(UPPER_BOUND_METRICS)
    if not required <= window.metrics.keys() or any(not isinstance(window.metrics[k], (int,float)) or isinstance(window.metrics[k], bool) or window.metrics[k] < 0 for k in required):
        raise MonitoringError("required metrics missing or invalid")
    alerts: list[Alert] = []
    for metric in sorted(CRITICAL_ZERO_TOLERANCE):
        observed = window.metrics[metric]
        if observed > 0: alerts.append(Alert(f"zero_tolerance.{metric}", "critical", metric, str(observed), "0"))
    for metric, minimum in sorted(LOWER_BOUND_METRICS.items()):
        observed = window.metrics[metric]
        if observed < minimum: alerts.append(Alert(f"quality.{metric}", "warning", metric, str(observed), f">={minimum}"))
    for metric, maximum in sorted(UPPER_BOUND_METRICS.items()):
        observed = window.metrics[metric]
        if observed > maximum: alerts.append(Alert(f"slo.{metric}", "warning", metric, str(observed), f"<={maximum}"))
    if window.model_id != baseline.model_id: alerts.append(Alert("drift.model_id", "critical", "model_id", window.model_id, baseline.model_id))
    if window.prompt_version != baseline.prompt_version: alerts.append(Alert("drift.prompt_version", "critical", "prompt_version", window.prompt_version, baseline.prompt_version))
    if window.config_fingerprint != baseline.config_fingerprint: alerts.append(Alert("drift.config_fingerprint", "critical", "config_fingerprint", window.config_fingerprint, baseline.config_fingerprint))
    for metric, approved in sorted(baseline.approved_metrics.items()):
        if metric in window.metrics and approved > 0 and abs(window.metrics[metric]-approved)/approved > 0.20:
            alerts.append(Alert(f"statistical_drift.{metric}", "warning", metric, str(window.metrics[metric]), f"within_20_percent_of_{approved}"))
    alerts = sorted(alerts, key=lambda item: (0 if item.severity=="critical" else 1,item.code))
    critical = any(item.severity == "critical" for item in alerts)
    status = "critical" if critical else "degraded" if alerts else "healthy"
    traffic = "safe_fallback" if critical else "increase_review" if alerts else "continue"
    execution = "freeze_automated_execution" if critical else "require_extra_review" if alerts else "continue"
    payload = {"baseline":baseline.baseline_id,"window":window.window_id,"tenant":window.tenant_id,"alerts":[item.__dict__ for item in alerts],"status":status,"trace":window.trace_head_sha256}
    return MonitoringDecision(status,tuple(alerts),traffic,execution,hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest())


def supervisor_controls(decision: MonitoringDecision) -> dict[str, object]:
    return {"agent_health_status":decision.status,"agent_traffic_action":decision.traffic_action,"agent_execution_action":decision.execution_action,"agent_monitoring_provenance_sha256":decision.provenance_sha256,"safe_fallback_policy":"deterministic_triage_and_human_review" if decision.status=="critical" else None}
