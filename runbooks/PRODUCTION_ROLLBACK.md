# Production Rollback

Rollback is a precondition, not a post-failure improvisation.

- Retain the exact previously accepted image digests.
- Never roll back to a schema-incompatible binary.
- Stop promotion immediately when a rollback trigger fires.
- Freeze new mutating remediation while rollback is in progress when safe to do so.
- Restore the previous deployment revision/digest.
- Run production-safe smoke tests and tenant-isolation probes.
- Confirm queue/checkpoint compatibility and no orphaned remediation execution.
- Verify observability and incident audit continuity.
- If data restoration is required, use the approved DR runbook and measure RPO/RTO.
- Record the decision, operator, timestamps, evidence hashes and follow-up incident/problem record.
