from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import GateStatus, ReleaseBlockerReport, ScenarioResult


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_prior_gate_statuses(project_root: Path) -> tuple[GateStatus, ...]:
    backend = project_root / "backend"
    quality_path = backend / "evals" / "QUALITY_CERTIFICATION_REPORT.json"
    performance_path = backend / "evals" / "PERFORMANCE_CERTIFICATION.json"
    security_path = backend / "redteam" / "reports" / "SECURITY_CERTIFICATION.json"

    quality = _load_json(quality_path)
    performance = _load_json(performance_path)
    security = _load_json(security_path)

    quality_cert = dict(quality["release_certificate"])
    perf_cert = dict(performance["certificate"])
    security_cert = dict(security["certificate"])

    return (
        GateStatus(
            "observability_quality_llmops",
            bool(quality_cert.get("passed")),
            str(quality_path.relative_to(project_root)),
            str(quality_cert.get("fingerprint") or ""),
        ),
        GateStatus(
            "performance_capacity",
            bool(perf_cert.get("passed")),
            str(performance_path.relative_to(project_root)),
            str(perf_cert.get("fingerprint") or ""),
            tuple(str(x) for x in perf_cert.get("warnings", [])),
        ),
        GateStatus(
            "security_adversarial",
            bool(security_cert.get("passed")),
            str(security_path.relative_to(project_root)),
            str(security_cert.get("fingerprint") or ""),
            tuple(str(x) for x in security_cert.get("warnings", [])),
        ),
    )


def build_final_report(
    *,
    project_root: Path,
    scenario_results: Iterable[ScenarioResult],
    reset_verified: bool,
    contract_passed: bool,
    accessibility_passed: bool,
    failure_recovery_passed: bool,
) -> ReleaseBlockerReport:
    prior = list(load_prior_gate_statuses(project_root))
    prior.extend(
        [
            GateStatus("frontend_backend_contracts", contract_passed, "e2e-static-contract-check"),
            GateStatus("accessibility_contracts", accessibility_passed, "accessibility-e2e-contract"),
            GateStatus("failure_recovery", failure_recovery_passed, "recovery-e2e-contract"),
        ]
    )
    return ReleaseBlockerReport.build(
        gates=tuple(prior),
        scenarios=tuple(scenario_results),
        reset_verified=reset_verified,
        metadata={
            "release_stage": "end-to-end",
            "kind": "synthetic-final-e2e-certification",
            "scope": "recruiter demo and production scenario regression",
        },
    )
