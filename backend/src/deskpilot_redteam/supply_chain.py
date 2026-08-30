from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import tomllib


@dataclass(frozen=True, slots=True)
class SupplyChainFinding:
    severity: str
    code: str
    path: str
    detail: str


@dataclass(frozen=True, slots=True)
class SupplyChainReport:
    findings: tuple[SupplyChainFinding, ...]

    @property
    def blocking(self) -> tuple[SupplyChainFinding, ...]:
        return tuple(row for row in self.findings if row.severity in {"high", "critical"})


_EXACT_NPM = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
_EXACT_PY = re.compile(r"^[A-Za-z0-9_.-]+==[^=<>~!]+$")


class SupplyChainScanner:
    """Static artifact policy. Live CVE/malware intelligence remains a CI/staging concern."""

    def scan(self, root: Path) -> SupplyChainReport:
        findings: list[SupplyChainFinding] = []
        package_json = root / "frontend" / "package.json"
        if package_json.exists():
            payload = json.loads(package_json.read_text())
            for section in ("dependencies", "devDependencies"):
                for name, version in payload.get(section, {}).items():
                    if section == "dependencies" and not _EXACT_NPM.fullmatch(str(version)):
                        findings.append(SupplyChainFinding("high", "npm_runtime_not_exact", str(package_json.relative_to(root)), f"{name}={version}"))
                    elif section == "devDependencies" and not _EXACT_NPM.fullmatch(str(version)):
                        findings.append(SupplyChainFinding("medium", "npm_dev_not_exact", str(package_json.relative_to(root)), f"{name}={version}"))
            if not (root / "frontend" / "package-lock.json").exists():
                findings.append(SupplyChainFinding("medium", "npm_lockfile_missing", "frontend/package-lock.json", "generate and commit lockfile in connected CI"))

        pyproject = root / "backend" / "pyproject.toml"
        if pyproject.exists():
            data = tomllib.loads(pyproject.read_text())
            optional = data.get("project", {}).get("optional-dependencies", {})
            for group, dependencies in optional.items():
                for dep in dependencies:
                    # The web adapter deliberately permits bounded compatible FastAPI ranges;
                    # test/observability production tooling should be exact.
                    if group in {"test", "observability"} and not _EXACT_PY.fullmatch(dep):
                        findings.append(SupplyChainFinding("medium", "python_optional_not_exact", str(pyproject.relative_to(root)), dep))

        for candidate in root.rglob("*.env"):
            if candidate.name != ".env.example":
                findings.append(SupplyChainFinding("high", "environment_secret_file", str(candidate.relative_to(root)), "unexpected environment file in artifact"))
        for candidate in root.rglob("*.pem"):
            findings.append(SupplyChainFinding("critical", "private_key_material", str(candidate.relative_to(root)), "key material must not ship in artifact"))
        return SupplyChainReport(tuple(findings))
