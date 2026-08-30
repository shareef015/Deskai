# Disaster Recovery Runbook — Connected staging

## Scope
Production-like staging exercise for PostgreSQL, Redis-dependent workflows, vector index restoration/rebuild, application configuration, audit continuity and deployment recovery.

## Default objectives
Treat these as initial staging targets until business owners approve final production objectives:
- PostgreSQL transactional data: RPO <= 5 minutes, RTO <= 30 minutes.
- Configuration/secret references: RPO <= 15 minutes, RTO <= 30 minutes.
- Vector index: recover from durable source corpus or snapshot; RTO <= 60 minutes.
- Redis/cache: no durable business-data dependency; rebuild after failover.

## Required drill
1. Capture immutable release, migration and data-backup identifiers.
2. Confirm backup completion before fault injection.
3. Simulate or execute an approved staging database loss/failover.
4. Restore into an isolated recovery target first.
5. Verify schema version, row counts, RLS policies, tenant isolation and audit-chain integrity.
6. Rebuild or restore vector indexes and rerun retrieval/citation golden tests.
7. Reconnect Redis and confirm stale cache/session artifacts cannot cross tenants.
8. Bring application replicas up against the recovered dependencies.
9. Run End-to-end golden scenarios and Security critical adversarial checks.
10. Measure observed data-loss window and recovery duration.
11. Record evidence and SHA-256 fingerprints.

## Fail conditions
The drill fails if RPO or RTO is exceeded, restore integrity is not verified, RLS is absent, audit integrity fails, tenant isolation fails, or application closure/remediation verification becomes unsafe.
