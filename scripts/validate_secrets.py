from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = ("BEGIN PRIVATE KEY", "AKIA", "sk-proj-", "ghp_")


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/secrets-and-certificates-policy.json").read_text())
    if set(policy["approved_providers"]) != {"env", "file", "vault"}:
        errors.append("secret provider allowlist changed")
    invariants = policy["invariants"]
    for key in ("plaintext_in_repository", "plaintext_in_logs_traces_errors_or_audit", "llm_secret_access", "private_key_export"):
        if invariants.get(key) is not False:
            errors.append(f"unsafe secret invariant: {key}")
    for key in ("provider_access_is_least_privilege", "rotation_is_audited"):
        if invariants.get(key) is not True:
            errors.append(f"missing secret invariant: {key}")
    source = ROOT / "packages/python/deskpilot-core/src/deskpilot_core/secrets.py"
    if not source.is_file():
        errors.append("secret resolver implementation missing")
    scanned = [path for path in ROOT.rglob("*") if path.is_file() and path.suffix in {".py", ".json", ".md", ".example"}]
    for path in scanned:
        text = path.read_text(encoding="utf-8", errors="ignore")
        is_validator = path.parent.name == "scripts" and path.name.startswith("validate_")
        if not is_validator and any(marker in text for marker in FORBIDDEN):
            errors.append(f"possible committed secret material: {path.relative_to(ROOT)}")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("secrets and certificates validation passed")
