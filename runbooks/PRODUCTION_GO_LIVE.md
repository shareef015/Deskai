# DeskPilot AI Production Go-Live Runbook

## Hard prerequisite
Do not promote anything to production until `backend/staging/reports/CONNECTED_STAGING_CERTIFICATION.json` reports `decision: pass` and `passed: true`.

## Human gates
1. Release authority reviews Connected staging connected evidence and approves go/no-go.
2. Database owner approves migration and rollback compatibility.
3. Security owner reviews Security + Connected staging penetration evidence.
4. Performance owner reviews Performance + connected Connected staging load/soak evidence.
5. Operations owner accepts dashboards, alerts, on-call, escalation and rollback authority.
6. Business/technical authority signs final operational acceptance after the observation window.

## Promotion sequence
1. Verify exact signed image digest from Connected staging; do not rebuild.
2. Verify production config references and KMS/Vault resolution.
3. Verify fresh backup and recovery evidence.
4. Verify rollback target and compatibility.
5. Apply approved migration job.
6. Deploy canary with bounded traffic.
7. Evaluate error rate, p95 latency, saturation, golden pass rate and AI groundedness.
8. Roll forward only when canary gate passes.
9. Complete rolling deployment.
10. Run non-destructive smoke/golden scenarios.
11. Verify traces/metrics/logs, SLOs and alerts.
12. Hold the observation window.
13. Collect immutable evidence and named approvals.
14. Run final Production certificate.

## Immediate rollback triggers
- cross-tenant exposure or authorization regression
- unauthorized remediation or HITL bypass
- critical/high security event linked to release
- sustained error rate or latency over release guardrails
- database integrity or migration anomaly
- golden scenario regression
- observability blind spot for critical path
- model/agent behavior outside governed quality threshold
- inability to verify rollback or restore
