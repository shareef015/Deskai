# DeskPilot AI Security Model — Through Security

DeskPilot AI applies defense-in-depth across browser, identity, API, tenant, AI and tool-execution boundaries.

## Browser and session

- restrictive CSP / Trusted Types contracts;
- CSRF-bound state-changing requests;
- secure session-cookie model;
- safe redirects and frontend sensitive-state redaction.

## Identity and authorization

- OIDC Authorization Code + PKCE contract;
- opaque server-side sessions with rotation/revocation;
- RBAC + ABAC and tenant-aware capabilities;
- step-up authentication for sensitive remediation;
- one-time approval and permission-drift controls.

## Backend and tenant isolation

- authenticated protected endpoints;
- tenant-scoped repository and PostgreSQL RLS contracts;
- BOLA/object-authorization defense;
- service identity and internal trust boundaries;
- rate limits, request validation, SSRF protection and safe errors.

## AI / RAG / agent / MCP

- retrieved content is untrusted data;
- prompt-injection filtering and citation integrity;
- tenant-scoped retrieval and context propagation;
- deterministic agent routing/loop budgets;
- explicit tool registration/capabilities;
- mutating MCP calls require governed human approval;
- verification must succeed before closure.

## Security adversarial certification

The release gate executes synthetic attacks across authentication, tenant escape, API abuse, SSRF, direct/indirect prompt injection, RAG poisoning, excessive agency, MCP/HITL bypass, privilege escalation, sensitive disclosure, resource exhaustion and malicious file handling.

Release requires 100% block rate for the defined critical/high matrix, zero sensitive-data disclosure, zero unauthorized mutation and zero cross-tenant exposure. High/critical static supply-chain findings also block release.

## Supply chain

Production runtime dependency versions are exact. Security also pins frontend development tooling. A resolver-generated npm lockfile and live vulnerability/advisory scan remain connected-CI gates and are not fabricated inside offline artifacts.

## Penetration-testing boundary

The included red-team suite is deterministic, synthetic and non-destructive. It does not replace an authorized human-led penetration test against the release candidate in a controlled staging environment.

## Connected staging connected-staging boundary

Production-like staging requires external KMS/Vault-managed secrets, default-deny networking, real tenant-isolation/RLS probes, authenticated MCP transports, staging-only Windows endpoints and explicitly authorized security testing. The repository does not authorize penetration testing of production, third-party or employee systems. Real secret values must never be committed; `infra/k8s/staging/runtime-secrets.example.yaml` contains placeholders only and is excluded from Kustomize.
