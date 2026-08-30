from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND / "src"))

from deskpilot_staging.certification import ConnectedStagingGate
from deskpilot_staging.evidence import load_evidence
from deskpilot_staging.preflight import validate_project_preflight


def main() -> int:
    preflight = validate_project_preflight(PROJECT_ROOT)
    evidence_path = BACKEND / "staging" / "evidence" / "connected-staging-evidence.json"
    evidence = load_evidence(evidence_path)
    certificate = ConnectedStagingGate().certify(project_root=PROJECT_ROOT, evidence=evidence)
    payload = {
        "schema_version": 1,
        "release_stage": "staging",
        "kind": "connected-staging-preflight",
        "preflight": asdict(preflight),
        "certificate": asdict(certificate),
        "evidence_path": str(evidence_path.relative_to(PROJECT_ROOT)),
        "limitations": [
            "This local preflight does not claim a connected staging deployment.",
            "A PASS release-candidate decision requires real staging evidence for every blocking control.",
            "Synthetic evidence cannot satisfy controls marked as requiring real evidence.",
        ],
    }
    out = BACKEND / "staging" / "reports" / "STAGING_PREFLIGHT.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0 if preflight.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
