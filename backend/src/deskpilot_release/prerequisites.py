from __future__ import annotations

import json
from pathlib import Path


def staging_connected_pass(project_root: Path) -> bool:
    path = project_root / "backend" / "staging" / "reports" / "CONNECTED_STAGING_CERTIFICATION.json"
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    certificate = dict(payload.get("certificate", {}))
    return bool(certificate.get("passed")) and certificate.get("decision") == "pass"


def staging_fingerprint(project_root: Path) -> str | None:
    path = project_root / "backend" / "staging" / "reports" / "CONNECTED_STAGING_CERTIFICATION.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    value = dict(payload.get("certificate", {})).get("fingerprint")
    return str(value) if value else None
