# Rolling Deployment and Rollback Runbook — Connected staging

## Rolling release gate
- All desired replicas become ready.
- Error rate <= 1% during rollout.
- API p95 <= 1500 ms during the drill.
- No more than one API replica unavailable at a time.
- No cross-tenant, auth, approval, citation or tool-authority regression.

## Rollback sequence
1. Freeze new mutating remediation if rollout health breaches the gate.
2. Preserve in-flight audit events and correlation IDs.
3. Roll application images back to the previously attested digest.
4. Do not blindly reverse a destructive schema migration. Use only explicitly tested backward-compatible/down migration procedures.
5. Wait for readiness and verify session/OIDC compatibility.
6. Run health, RLS, RAG, MCP read-only and streaming smoke tests.
7. Run at least one Printer and one Outlook golden scenario.
8. Re-enable mutating remediation only after independent verification passes.
9. Record rollout and rollback evidence with timestamps and fingerprints.
