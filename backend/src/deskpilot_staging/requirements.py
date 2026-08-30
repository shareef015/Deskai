from __future__ import annotations

from .models import ControlRequirement


CONNECTED_STAGING_REQUIREMENTS: tuple[ControlRequirement, ...] = (
    ControlRequirement("oidc_real_login", "Real OIDC Authorization Code + PKCE login/logout/step-up against staging IdP."),
    ControlRequirement("postgres_rls", "Live PostgreSQL RLS cross-tenant read/write denial with FORCE ROW LEVEL SECURITY."),
    ControlRequirement("redis_live", "Live Redis connectivity, tenant-safe keying, TTL and reconnect behavior."),
    ControlRequirement("vector_retrieval", "Live vector/hybrid retrieval against staging corpus with tenant filters and citations."),
    ControlRequirement("model_routing", "Live model-provider routing, timeout/fallback, token/cost and quality telemetry."),
    ControlRequirement("mcp_transport", "Authenticated MCP transport connectivity and tool authorization."),
    ControlRequirement("windows_printer", "Live staging Windows printer diagnostics/remediation/verification."),
    ControlRequirement("windows_outlook", "Live staging Windows Outlook diagnostics/remediation/verification."),
    ControlRequirement("sse_streaming", "Live SSE reconnect/resume and event-deduplication under connection interruption."),
    ControlRequirement("websocket_streaming", "Live WebSocket heartbeat/reconnect/fan-out verification."),
    ControlRequirement("otel_export", "Trace/metric/log export to production-like OpenTelemetry backend."),
    ControlRequirement("langsmith_export", "LangSmith trace/evaluation export with tenant-safe redaction."),
    ControlRequirement("autoscaling", "Kubernetes HPA/PDB behavior under load with bounded scale-up/down."),
    ControlRequirement("secrets_kms", "External secret/KMS resolution with no plaintext application secrets."),
    ControlRequirement("migrations", "Forward database migration and compatibility verification in staging."),
    ControlRequirement("backup_restore", "Database/config backup and restore drill with measured RPO/RTO."),
    ControlRequirement("rolling_deploy", "Zero/controlled-downtime rolling deployment validation."),
    ControlRequirement("rollback", "Application and schema-compatible rollback drill."),
    ControlRequirement("failover_dr", "Service/data failover or documented DR exercise with recovery evidence."),
    ControlRequirement("load_soak", "Connected load/stress/soak test against staging capacity envelope."),
    ControlRequirement("authorized_pentest", "Authorized staging penetration test / security review evidence."),
)
