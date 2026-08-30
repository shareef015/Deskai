from __future__ import annotations

from .models import ProductionControlRequirement


PRODUCTION_GO_LIVE_REQUIREMENTS: tuple[ProductionControlRequirement, ...] = (
    ProductionControlRequirement(
        "human_go_no_go",
        "Named release authority approves the production promotion after reviewing Connected staging connected evidence.",
        requires_human_approval=True,
    ),
    ProductionControlRequirement(
        "production_config_secrets",
        "Production configuration and external KMS/Vault secret references are verified with no plaintext secrets.",
    ),
    ProductionControlRequirement(
        "signed_artifact_promotion",
        "Exactly the Connected staging-certified signed/attested image digests are promoted without rebuild or mutable tags.",
    ),
    ProductionControlRequirement(
        "migration_approval",
        "Production migration plan, compatibility window and rollback path are human-approved before execution.",
        requires_human_approval=True,
    ),
    ProductionControlRequirement(
        "canary_release",
        "Canary receives bounded traffic and satisfies error, latency, saturation and AI-quality guardrails.",
    ),
    ProductionControlRequirement(
        "rolling_release",
        "Production rollout completes within availability/error budgets with no unsafe capacity degradation.",
    ),
    ProductionControlRequirement(
        "production_smoke_golden",
        "Production-safe smoke and golden scenarios pass without destructive or cross-tenant side effects.",
    ),
    ProductionControlRequirement(
        "live_observability_slo",
        "Production traces, metrics, logs, alerts and SLO/error-budget views are live and correlated end-to-end.",
    ),
    ProductionControlRequirement(
        "rollback_readiness",
        "Rollback target, command path, schema compatibility and operator authority are verified immediately before release.",
    ),
    ProductionControlRequirement(
        "backup_dr_confirmation",
        "Fresh backup, restore integrity, RPO/RTO and DR evidence remain valid for the production release window.",
    ),
    ProductionControlRequirement(
        "security_evidence_review",
        "Security adversarial evidence and Connected staging authorized staging penetration evidence are reviewed with no open critical/high blocker.",
        requires_human_approval=True,
    ),
    ProductionControlRequirement(
        "performance_evidence_review",
        "Performance capacity evidence and Connected staging connected load/soak evidence are reviewed against the production envelope.",
        requires_human_approval=True,
    ),
    ProductionControlRequirement(
        "operator_handover",
        "On-call ownership, runbooks, escalation, rollback authority, dashboards and incident response are accepted by operators.",
        requires_human_approval=True,
    ),
    ProductionControlRequirement(
        "recruiter_portfolio_package",
        "Recruiter-facing package is sanitized, synthetic-only, reproducible and contains no production credentials/evidence secrets.",
    ),
    ProductionControlRequirement(
        "final_operational_acceptance",
        "Named business/technical release authority signs final production acceptance after the observation window.",
        requires_human_approval=True,
    ),
)
