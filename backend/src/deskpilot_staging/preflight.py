from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PreflightResult:
    passed: bool
    failures: tuple[str, ...]
    warnings: tuple[str, ...]


def validate_project_preflight(project_root: Path) -> PreflightResult:
    required = (
        project_root / "backend" / "demo" / "reports" / "E2E_CERTIFICATION.json",
        project_root / "infra" / "k8s" / "staging" / "kustomization.yaml",
        project_root / "runbooks" / "STAGING_DEPLOYMENT.md",
        project_root / "runbooks" / "DISASTER_RECOVERY.md",
        project_root / "runbooks" / "ROLLBACK.md",
    )
    failures = [f"missing:{path.relative_to(project_root)}" for path in required if not path.exists()]
    warnings: list[str] = []
    if not (project_root / "frontend" / "package-lock.json").exists():
        warnings.append("npm_lockfile_missing_connected_ci_required")
    return PreflightResult(not failures, tuple(failures), tuple(warnings))
