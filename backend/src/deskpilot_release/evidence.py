from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from .models import ProductionEvidenceItem, ProductionEvidenceStatus


def load_production_evidence(path: Path) -> tuple[ProductionEvidenceItem, ...]:
    if not path.exists():
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: list[ProductionEvidenceItem] = []
    for item in payload.get("evidence", []):
        result.append(
            ProductionEvidenceItem(
                control_id=str(item["control_id"]),
                status=ProductionEvidenceStatus(str(item.get("status", "not_run"))),
                source=str(item.get("source", "")),
                observed_at=item.get("observed_at"),
                fingerprint=item.get("fingerprint"),
                approver=item.get("approver"),
                notes=tuple(str(x) for x in item.get("notes", [])),
                environment=str(item.get("environment", "production")),
            )
        )
    return tuple(result)


def write_production_evidence(path: Path, evidence: tuple[ProductionEvidenceItem, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "release_stage": "production", "evidence": [asdict(item) for item in evidence]}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
