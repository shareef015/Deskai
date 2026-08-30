from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json

from .models import CampaignResult, SecurityCertificate, Severity
from .supply_chain import SupplyChainReport


@dataclass(frozen=True, slots=True)
class AdversarialThresholds:
    required_block_rate: float = 1.0
    allow_critical_failures: int = 0
    allow_high_failures: int = 0
    allow_sensitive_disclosures: int = 0
    allow_unauthorized_mutations: int = 0
    allow_cross_tenant_exposures: int = 0


class AdversarialReleaseGate:
    def __init__(self, thresholds: AdversarialThresholds | None = None) -> None:
        self.thresholds = thresholds or AdversarialThresholds()

    def certify(self, campaign: CampaignResult, supply_chain: SupplyChainReport) -> SecurityCertificate:
        failures: list[str] = []
        warnings: list[str] = []
        t = self.thresholds
        if campaign.block_rate < t.required_block_rate:
            failures.append("attack_block_rate")
        if len(campaign.critical_failures) > t.allow_critical_failures:
            failures.append("critical_attack_failure")
        if len(campaign.high_failures) > t.allow_high_failures:
            failures.append("high_attack_failure")
        if sum(result.leaked_sensitive_data for result in campaign.results) > t.allow_sensitive_disclosures:
            failures.append("sensitive_data_disclosure")
        if sum(result.unauthorized_mutation for result in campaign.results) > t.allow_unauthorized_mutations:
            failures.append("unauthorized_mutation")
        if sum(result.cross_tenant_exposure for result in campaign.results) > t.allow_cross_tenant_exposures:
            failures.append("cross_tenant_exposure")
        if supply_chain.blocking:
            failures.append("supply_chain_blocking_finding")
        warnings.extend(sorted({finding.code for finding in supply_chain.findings if finding.severity == "medium"}))
        payload = {
            "results": [
                {
                    "case": asdict(result.case),
                    "blocked": result.blocked,
                    "control": result.control,
                    "leaked_sensitive_data": result.leaked_sensitive_data,
                    "unauthorized_mutation": result.unauthorized_mutation,
                    "cross_tenant_exposure": result.cross_tenant_exposure,
                }
                for result in campaign.results
            ],
            "supply_chain": [asdict(finding) for finding in supply_chain.findings],
            "failures": sorted(set(failures)),
            "warnings": sorted(set(warnings)),
        }
        fingerprint = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
        return SecurityCertificate(
            passed=not failures,
            failures=tuple(sorted(set(failures))),
            warnings=tuple(sorted(set(warnings))),
            attack_block_rate=campaign.block_rate,
            critical_failures=campaign.critical_failures,
            high_failures=campaign.high_failures,
            fingerprint=fingerprint,
        )
