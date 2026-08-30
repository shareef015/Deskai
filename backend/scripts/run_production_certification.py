from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND / "src"))

from deskpilot_release.certification import FinalProductionGate
from deskpilot_release.evidence import load_production_evidence


def main() -> int:
    evidence_path = BACKEND / "production" / "evidence" / "production-go-live-evidence.json"
    evidence = load_production_evidence(evidence_path)
    certificate = FinalProductionGate().certify(project_root=PROJECT_ROOT, evidence=evidence)
    payload = {
        "schema_version": 1,
        "release_stage": "production",
        "kind": "final-production-operational-acceptance",
        "certificate": asdict(certificate),
        "evidence": [asdict(item) for item in evidence],
    }
    out = BACKEND / "production" / "reports" / "PRODUCTION_CERTIFICATION.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(payload["certificate"], indent=2, sort_keys=True, default=str))
    return 0 if certificate.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
