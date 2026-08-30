from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from deskpilot_redteam.campaign import run_default_campaign
from deskpilot_redteam.certification import AdversarialReleaseGate
from deskpilot_redteam.supply_chain import SupplyChainScanner


def main() -> int:
    campaign = run_default_campaign()
    supply_chain = SupplyChainScanner().scan(ROOT)
    certificate = AdversarialReleaseGate().certify(campaign, supply_chain)
    payload = {
        "release_stage": "security",
        "scope": "production security, penetration, AI red-team and adversarial certification",
        "attack_summary": {
            "total": campaign.total,
            "blocked": campaign.blocked,
            "block_rate": campaign.block_rate,
            "critical_failures": list(campaign.critical_failures),
            "high_failures": list(campaign.high_failures),
        },
        "attacks": [
            {
                "id": result.case.attack_id,
                "title": result.case.title,
                "surface": result.case.surface.value,
                "severity": result.case.severity.value,
                "framework_refs": list(result.case.framework_refs),
                "expected_control": result.case.expected_control,
                "blocked": result.blocked,
                "evidence": result.evidence,
            }
            for result in campaign.results
        ],
        "supply_chain_findings": [asdict(row) for row in supply_chain.findings],
        "certificate": asdict(certificate),
        "limitations": [
            "Synthetic/local adversarial certification does not replace an authorized external penetration test.",
            "No destructive payloads or attacks against third-party systems are executed.",
            "Live IdP, PostgreSQL/Redis, vector store, model provider, MCP transport and Windows endpoints require staging validation.",
            "Live dependency vulnerability/malware intelligence requires connected CI scanners and registry advisories.",
        ],
    }
    destination = ROOT / "backend" / "redteam" / "reports" / "SECURITY_CERTIFICATION.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload["attack_summary"], sort_keys=True))
    print(f"passed={certificate.passed} fingerprint={certificate.fingerprint}")
    print(f"report={destination}")
    return 0 if certificate.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
