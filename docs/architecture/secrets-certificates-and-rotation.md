# Secrets, certificates and rotation

DeskPilot stores references—not secret values—in configuration. Services resolve
only the credentials they require at startup through an approved environment,
mounted-file, Vault, or customer cloud-secret adapter. Missing, empty, malformed,
out-of-scope, or expired material prevents readiness.

## Trust and access rules

- The API, worker, AI, RAG and MCP services use separate identities and policies.
- The LLM, prompts, retrieved documents and endpoint tool arguments never receive
  platform credentials or private keys.
- File-backed secrets must be below deployment-approved read-only mount roots.
- Certificate private keys are non-exportable or referenced through the secret
  control plane; endpoint communication uses mutual TLS.
- Logs, errors, traces, audit records and configuration fingerprints contain only
  reference type, logical identifier, version, outcome and correlation metadata.
- Rotation uses an overlap window, activates a new version, validates dependent
  health, revokes the old version and records immutable audit events.

## Provider contract

`SecretResolver` parses an allowlisted URI and dispatches to the corresponding
provider. Production deployments register only customer-approved adapters. Vault
and cloud implementations must authenticate with workload identity, restrict paths
per service, avoid persistent local caching and return the same redacted value type.

## Failure behavior

Resolution errors are deliberately generic and never include the reference path or
value. Readiness remains false when required material is absent or expired. Rotation
failure retains the last valid version during the bounded overlap window and alerts
an operator; it never silently falls back to embedded defaults.
