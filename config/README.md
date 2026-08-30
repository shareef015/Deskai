# Configuration

Environment profiles are explicit JSON inputs validated before service readiness.
Production rejects debug/docs/synthetic operation and resolves secrets only through
approved `env://`, `file://`, or `vault://` references. Runtime configuration is
immutable; activating a new approved release requires a restart and an audit event.

Use `environment.example` only as a deployment-variable name template. Never commit
real credentials, certificates, private keys, tokens, or customer identifiers.

Only non-secret templates are committed. Runtime secrets come from the deployment secret store.
