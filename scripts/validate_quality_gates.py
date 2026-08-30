from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> list[str]:
    errors: list[str] = []
    policy = json.loads((ROOT / "contracts/engineering-quality-policy.json").read_text())
    if policy.get("enforcement") != "required":
        errors.append("quality enforcement must be required")
    required_jobs = set(policy.get("ci", {}).get("required_jobs", []))
    workflow = (ROOT / ".github/workflows/quality.yml").read_text()
    for job in required_jobs:
        if f"  {job}:" not in workflow:
            errors.append(f"CI job missing: {job}")
    for command in ("ruff check .", "ruff format --check .", "mypy ", "npm run lint", "npm run typecheck", "gitleaks/gitleaks-action", "pip-audit", "npm audit"):
        if command not in workflow:
            errors.append(f"quality command missing: {command}")
    if "permissions:\n  contents: read" not in workflow:
        errors.append("CI permissions are not least privilege")
    if policy.get("exceptions", {}).get("silent_bypass_allowed") is not False:
        errors.append("silent gate bypass must be prohibited")
    for path in (".pre-commit-config.yaml", ".gitleaks.toml", "apps/web/eslint.config.mjs", "services/api/requirements.lock"):
        if not (ROOT / path).is_file():
            errors.append(f"quality artifact missing: {path}")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        raise SystemExit("\n".join(failures))
    print("engineering quality gates validation passed")
