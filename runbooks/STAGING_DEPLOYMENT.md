# Connected Staging Deployment Runbook — Connected staging

## Purpose
Deploy DeskPilot AI to a production-like staging environment and collect immutable evidence for the Connected staging release-candidate gate. This runbook is intentionally provider-neutral: substitute the actual registry, DNS, IdP, managed PostgreSQL/Redis/vector service, model provider, KMS/Vault, observability backend, MCP hosts and Windows staging devices.

## Preconditions
1. End-to-end certificate is passing.
2. A resolver-generated `frontend/package-lock.json` exists and connected CI passes `npm ci`, typecheck, tests, build and Playwright.
3. Container images are built from the release commit, vulnerability-scanned, signed/attested and pushed to the staging registry.
4. `deskpilot-runtime-secrets` is provisioned from an external secret/KMS system; do not apply `runtime-secrets.example.yaml` with real values committed to Git.
5. Staging DNS/TLS and a namespace-scoped Kubernetes context are ready.
6. Real staging tenants, users, Windows 10/11 devices, printer queues and Outlook profiles are synthetic/non-production.
7. Penetration testing is explicitly authorized for the staging scope.

## Deployment sequence
1. Pin release image digests in the staging manifests.
2. Run `kubectl kustomize infra/k8s/staging` and policy/lint validation.
3. Apply namespace/config/network/security resources.
4. Resolve external secrets and verify no plaintext secret is present in ConfigMaps or manifests.
5. Run the migration Job and record migration version/hash.
6. Deploy API, frontend and workers.
7. Wait for readiness and run the smoke-test Job.
8. Verify OIDC login/logout/step-up with a real staging IdP.
9. Run RLS cross-tenant read and write probes against staging PostgreSQL.
10. Verify Redis reconnect/TTL and vector retrieval/citation behavior.
11. Exercise live model routing and capture latency/token/cost/quality traces.
12. Exercise authenticated MCP transport with read-only diagnostics first.
13. With HITL approval, run bounded printer and Outlook remediation on synthetic staging devices and independently verify results.
14. Exercise SSE and WebSocket disconnect/reconnect/resume behavior.
15. Verify OpenTelemetry and LangSmith export with redaction.
16. Run connected performance/load/soak tests and observe HPA/PDB behavior.
17. Perform rolling update and rollback drills.
18. Perform backup/restore and failover/DR drills per `DISASTER_RECOVERY.md`.
19. Complete authorized staging penetration/security testing.
20. Record every control in `backend/staging/evidence/connected-staging-evidence.json` with immutable evidence fingerprint.
21. Run `python backend/scripts/run_connected_staging_certification.py`.

## Promotion rule
Only a Connected staging certificate with `decision=pass` is eligible for Production. `ready_for_connected_staging` means assets are ready but live validation has not occurred. `blocked` means one or more connected controls failed, used synthetic evidence, used the wrong environment, or remain missing.
