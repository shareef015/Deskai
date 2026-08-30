from __future__ import annotations

from dataclasses import dataclass
import re


_SHA256_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class ArtifactPromotion:
    staging_digest: str
    production_digest: str
    signature_verified: bool
    provenance_verified: bool
    rebuilt: bool = False


def certify_artifact_promotion(promotion: ArtifactPromotion) -> tuple[bool, tuple[str, ...]]:
    failures: list[str] = []
    if not _SHA256_DIGEST.fullmatch(promotion.staging_digest):
        failures.append("invalid_staging_digest")
    if not _SHA256_DIGEST.fullmatch(promotion.production_digest):
        failures.append("invalid_production_digest")
    if promotion.staging_digest != promotion.production_digest:
        failures.append("digest_changed")
    if not promotion.signature_verified:
        failures.append("signature_not_verified")
    if not promotion.provenance_verified:
        failures.append("provenance_not_verified")
    if promotion.rebuilt:
        failures.append("artifact_rebuilt_after_staging")
    return (not failures, tuple(failures))
