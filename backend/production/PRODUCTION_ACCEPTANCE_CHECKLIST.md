# Production Production Acceptance Checklist

## Prerequisite
- [ ] Connected staging connected certificate is PASS.

## Release authority
- [ ] Human go/no-go approval recorded.
- [ ] Exact Connected staging-certified image digest selected.
- [ ] Signature/provenance verified.
- [ ] No post-staging rebuild.

## Configuration and data
- [ ] Production config verified.
- [ ] KMS/Vault secret resolution verified.
- [ ] Migration explicitly approved.
- [ ] Fresh backup verified.
- [ ] Restore/DR evidence still within release window.
- [ ] Rollback target verified.

## Deployment
- [ ] Canary gate passes.
- [ ] Rolling deployment passes.
- [ ] Smoke tests pass.
- [ ] Production-safe golden tests pass.
- [ ] SLO/observability live.

## Governance
- [ ] Security evidence reviewed.
- [ ] Performance evidence reviewed.
- [ ] Operator handover signed.
- [ ] Recruiter package sanitized and synthetic-only.
- [ ] Observation window completed.
- [ ] Final operational acceptance signed.
