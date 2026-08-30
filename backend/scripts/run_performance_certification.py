from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deskpilot_performance.certification import PerformanceGate
from deskpilot_performance.simulation import DEFAULT_ENVELOPE, DEFAULT_STAGE_BUDGETS, synthetic_baseline


def main() -> int:
    scenario = synthetic_baseline()
    certificate = PerformanceGate(DEFAULT_STAGE_BUDGETS).certify(scenario, DEFAULT_ENVELOPE)
    payload = {
        "kind": "synthetic-regression-certificate",
        "disclaimer": "Deterministic regression envelope only; not a live infrastructure capacity claim.",
        "scenario": asdict(scenario),
        "certificate": asdict(certificate),
    }
    output = ROOT / "evals" / "PERFORMANCE_CERTIFICATION.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if certificate.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
