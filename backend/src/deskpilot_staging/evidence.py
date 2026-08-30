from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from .models import EvidenceItem, EvidenceStatus


def fingerprint_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def load_evidence(path: Path) -> tuple[EvidenceItem, ...]:
    if not path.exists():
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("evidence", [])
    result: list[EvidenceItem] = []
    for item in items:
        result.append(
            EvidenceItem(
                control_id=str(item["control_id"]),
                status=EvidenceStatus(str(item.get("status", "not_run"))),
                source=str(item.get("source", "")),
                observed_at=item.get("observed_at"),
                fingerprint=item.get("fingerprint"),
                notes=tuple(str(x) for x in item.get("notes", [])),
                environment=str(item.get("environment", "staging")),
            )
        )
    return tuple(result)


def write_evidence(path: Path, evidence: tuple[EvidenceItem, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "evidence": [asdict(item) for item in evidence]}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
