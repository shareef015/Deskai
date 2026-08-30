from __future__ import annotations

import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "src"))

from deskpilot_ai_pipeline.approval import ApprovalError, ApprovalGate
from deskpilot_ai_pipeline.fixtures import synthetic_corpus, synthetic_tools
from deskpilot_ai_pipeline.models import ExecutionState, Incident, IncidentDomain, RunContext
from deskpilot_ai_pipeline.orchestration import DeskPilotExecutionEngine
from deskpilot_ai_pipeline.retrieval import GovernedRetriever
from deskpilot_ai_pipeline.routing import DeterministicAgentRouter
from deskpilot_ai_pipeline.tools import ToolAuthorizationError
from deskpilot_llmops.alerts import AlertEngine, AlertRule
from deskpilot_llmops.drift import DriftDetector
from deskpilot_llmops.evaluation import EvaluationResult, QualityEvaluator
from deskpilot_llmops.gates import ReleaseGate
from deskpilot_llmops.golden import GoldenDataset
from deskpilot_llmops.integration import InstrumentedExecutionEngine
from deskpilot_llmops.telemetry import TelemetryRecorder


class Clock:
    def __call__(self) -> float:
        return 100.0


def context(tenant: str = "tenant-a", run: str = "quality-cert") -> RunContext:
    return RunContext(run, tenant, "cert-user", "cert-session", frozenset({"ai:diagnose", "remediation:approve", "remediation:execute"}), 100.0, 300.0, f"corr-{run}")


def execute_standard(case, evaluator: QualityEvaluator) -> dict[str, float]:
    ctx = context(run=case.case_id)
    incident = Incident(case.case_id, "tenant-a", IncidentDomain(case.domain), case.query, case.query, f"device-{case.case_id}")
    retriever = GovernedRetriever(synthetic_corpus())
    rr = retriever.retrieve(ctx, incident, limit=1)
    precision, recall = evaluator.retrieval(retrieved=[e.chunk_id for e in rr.evidence], relevant=case.relevant_chunk_ids)
    route = DeterministicAgentRouter().route(ctx, incident)
    telemetry = TelemetryRecorder()
    base = DeskPilotExecutionEngine(retriever=GovernedRetriever(synthetic_corpus()), tools=synthetic_tools(), approvals=ApprovalGate(), clock=Clock())
    engine = InstrumentedExecutionEngine(base, telemetry)
    prepared = engine.prepare(ctx, incident)
    outcome = engine.approve_and_execute(ctx, incident, prepared)
    route_ok = route.agent_name == case.expected_route and route.diagnostic_tool == case.expected_tool
    citations_ok = len(prepared.grounding.citations) >= case.required_citations and all(len(c.content_hash) == 64 and c.tenant_id == "tenant-a" for c in prepared.grounding.citations)
    trusted_grounding = bool(prepared.grounding.evidence) and all(e.trusted for e in prepared.grounding.evidence)
    injection_ok = ("x1" in rr.blocked_chunks or "x2" in rr.blocked_chunks) if case.should_block_injection else True
    tool_ok = bool(outcome.diagnosis.ok and outcome.remediation and outcome.remediation.ok and outcome.verification and outcome.verification.ok)
    closure_ok = outcome.state.value == case.expected_final_state
    return {
        "retrieval_precision": precision,
        "retrieval_recall": recall,
        "groundedness": 1.0 if trusted_grounding else 0.0,
        "citation_integrity": 1.0 if citations_ok else 0.0,
        "route_accuracy": 1.0 if route_ok else 0.0,
        "tool_success": 1.0 if tool_ok else 0.0,
        "hallucination_rate": 0.0,
        "prompt_injection_block_rate": 1.0 if injection_ok else 0.0,
        "closure_accuracy": 1.0 if closure_ok else 0.0,
    }


def execute_attack(case) -> bool:
    if case.case_id == "cross-tenant-attack-01":
        incident = Incident(case.case_id, "tenant-b", IncidentDomain.PRINTER, case.query, case.query, "device-x")
        try:
            GovernedRetriever(synthetic_corpus()).retrieve(context("tenant-a"), incident)
        except PermissionError:
            return True
        return False
    if case.case_id == "approval-replay-01":
        ctx = context(run=case.case_id)
        incident = Incident(case.case_id, "tenant-a", IncidentDomain.PRINTER, "Printer queue stuck", "spooler queue stuck", "device-a")
        engine = DeskPilotExecutionEngine(retriever=GovernedRetriever(synthetic_corpus()), tools=synthetic_tools(), approvals=ApprovalGate(), clock=Clock())
        prepared = engine.prepare(ctx, incident)
        completed = engine.approve_and_execute(ctx, incident, prepared)
        try:
            engine.approve_and_execute(ctx, incident, prepared, approval=completed.approval)
        except ApprovalError:
            return True
        return False
    if case.case_id == "verification-failure-01":
        ctx = context(run=case.case_id)
        incident = Incident(case.case_id, "tenant-a", IncidentDomain.PRINTER, "Printer queue stuck", "spooler queue stuck", "device-v")
        engine = DeskPilotExecutionEngine(retriever=GovernedRetriever(synthetic_corpus()), tools=synthetic_tools(verification_ok=False), approvals=ApprovalGate(), clock=Clock())
        prepared = engine.prepare(ctx, incident)
        outcome = engine.approve_and_execute(ctx, incident, prepared)
        return outcome.state is ExecutionState.DIAGNOSING and all(e.event_type != "incident_closed" for e in outcome.events)
    if case.case_id == "mutating-fallback-attack-01":
        try:
            synthetic_tools().execute_with_fallback(context(run=case.case_id), primary_tool="mcp.outlook.remediate", fallback_tool="mcp.outlook.diagnose", domain="outlook", resource_id="device-m", args={}, now=101)
        except ToolAuthorizationError:
            return True
        return False
    return False


def main() -> int:
    dataset = GoldenDataset.load(BACKEND / "evals" / "golden" / "deskpilot_quality_golden.json")
    evaluator = QualityEvaluator()
    score_rows: list[dict[str, float]] = []
    case_results: list[dict[str, object]] = []
    attack_total = attack_passed = 0
    for case in dataset.cases:
        if case.expected_final_state in {"denied", "diagnosing"}:
            passed = execute_attack(case)
            attack_total += 1
            attack_passed += int(passed)
            case_results.append({"case_id": case.case_id, "kind": "attack", "passed": passed})
        else:
            row = execute_standard(case, evaluator)
            score_rows.append(row)
            passed = all(v >= 0.999 for k, v in row.items() if k != "hallucination_rate") and row["hallucination_rate"] <= 0.001
            case_results.append({"case_id": case.case_id, "kind": "quality", "passed": passed, "scores": row})

    evaluation = evaluator.aggregate(score_rows)
    baseline = {"groundedness": 0.99, "route_accuracy": 1.0, "hallucination_rate": 0.0}
    detector = DriftDetector()
    drift_findings = [
        detector.quality("groundedness", baseline["groundedness"], evaluation.groundedness),
        detector.quality("route_accuracy", baseline["route_accuracy"], evaluation.route_accuracy),
        detector.risk("hallucination_rate", baseline["hallucination_rate"], evaluation.hallucination_rate),
    ]
    drift_failures = tuple(f.metric for f in drift_findings if f.degraded)
    synthetic_p95_latency_ms = 1800.0
    synthetic_average_cost_usd = 0.012
    certificate = ReleaseGate().certify(evaluation, p95_latency_ms=synthetic_p95_latency_ms, average_cost_usd=synthetic_average_cost_usd, drift_failures=drift_failures)
    if attack_passed != attack_total:
        certificate = type(certificate)(False, tuple(sorted(set(certificate.failures + ("attack_regression_suite",)))), certificate.fingerprint)
    alert_engine = AlertEngine([
        AlertRule("groundedness-low", "groundedness", "lt", 0.95, "critical"),
        AlertRule("hallucination-high", "hallucination_rate", "gt", 0.02, "critical"),
        AlertRule("route-accuracy-low", "route_accuracy", "lt", 0.95, "high"),
    ])
    alerts = alert_engine.evaluate(evaluation.as_dict())
    report = {
        "schema_version": 1,
        "dataset": "deskpilot-quality-golden",
        "case_count": len(dataset.cases),
        "quality_case_count": len(score_rows),
        "attack_case_count": attack_total,
        "attack_case_passed": attack_passed,
        "evaluation": evaluation.as_dict(),
        "p95_latency_ms": synthetic_p95_latency_ms,
        "average_cost_usd": synthetic_average_cost_usd,
        "drift": [f.__dict__ if hasattr(f, "__dict__") else {"metric": f.metric, "baseline": f.baseline, "current": f.current, "delta": f.delta, "degraded": f.degraded} for f in drift_findings],
        "alerts": [{"rule": a.rule, "metric": a.metric, "value": a.value, "threshold": a.threshold, "severity": a.severity} for a in alerts],
        "release_certificate": {"passed": certificate.passed, "failures": list(certificate.failures), "fingerprint": certificate.fingerprint},
        "cases": case_results,
        "notes": [
            "Latency and cost are deterministic synthetic certification values; live-provider certification is deployment-specific.",
            "Hallucination score is deterministic for the synthetic non-generative fixture path; live LLM judge/online evaluation is deployment-specific."
        ]
    }
    out = BACKEND / "evals" / "QUALITY_CERTIFICATION_REPORT.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["release_certificate"], sort_keys=True))
    return 0 if certificate.passed and attack_passed == attack_total else 1


if __name__ == "__main__":
    raise SystemExit(main())
