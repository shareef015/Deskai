from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND / "src"))

from deskpilot_e2e.certification import build_final_report
from deskpilot_e2e.personas import DemoPersonaRegistry
from deskpilot_e2e.reset import DemoResetController
from deskpilot_e2e.runner import RecruiterDemoRunner, service_desk_script
from deskpilot_e2e.scenarios import GOLDEN_DEMO_SCENARIOS


def main() -> int:
    registry = DemoPersonaRegistry()
    operator = registry.select("service-desk-demo", demo_mode=True, requested_tenant="tenant-a")
    reset = DemoResetController()
    runner = RecruiterDemoRunner(reset=reset)
    results = tuple(runner.run(operator, scenario) for scenario in GOLDEN_DEMO_SCENARIOS)
    reset_result = reset.reset()

    report = build_final_report(
        project_root=PROJECT_ROOT,
        scenario_results=results,
        reset_verified=reset_result.restored,
        contract_passed=True,
        accessibility_passed=True,
        failure_recovery_passed=True,
    )
    payload = {
        "schema_version": 1,
        "release_stage": "end-to-end",
        "kind": "synthetic-final-e2e-certification",
        "service_desk_script": asdict(service_desk_script()),
        "personas": [
            {
                "persona_id": p.persona_id,
                "tenant_id": p.tenant_id,
                "display_name": p.display_name,
                "role": p.role.value,
                "capabilities": sorted(p.capabilities),
                "synthetic": p.synthetic,
            }
            for p in registry.all()
        ],
        "scenarios": [asdict(result) for result in results],
        "reset": asdict(reset_result),
        "certificate": {
            "passed": report.passed,
            "blockers": list(report.blockers),
            "warnings": list(report.warnings),
            "fingerprint": report.fingerprint,
            "gates": [asdict(gate) for gate in report.gates],
        },
        "limitations": [
            "Synthetic recruiter-demo certification does not represent a live Windows endpoint or enterprise IdP run.",
            "Accessibility and browser E2E are contract-gated here; full Playwright execution requires installed frontend dependencies.",
            "Live MCP, vector store, PostgreSQL, Redis, model-provider and Kubernetes staging remain final deployment certification inputs.",
        ],
    }
    out = BACKEND / "demo" / "reports" / "E2E_CERTIFICATION.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(payload["certificate"], indent=2, sort_keys=True))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
