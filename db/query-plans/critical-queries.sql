-- Run against representative synthetic data with EXPLAIN (ANALYZE, BUFFERS, WAL, FORMAT JSON).

-- Open incident work queue: keyset cursor is (opened_at, id).
SELECT id, status, priority, summary, opened_at
FROM incidents
WHERE tenant_id = :tenant_id
  AND closed_at IS NULL
  AND (opened_at, id) < (:cursor_opened_at, :cursor_id)
ORDER BY opened_at DESC, id DESC
LIMIT :limit;

-- Latest durable checkpoint for a resumable AI run.
SELECT id, checkpoint_sequence, state_reference, state_sha256, created_at
FROM ai_checkpoints
WHERE tenant_id = :tenant_id AND run_id = :run_id
ORDER BY checkpoint_sequence DESC
LIMIT 1;

-- Valid human approval for the exact immutable action fingerprint.
SELECT id, approver_id, decided_at, expires_at
FROM approval_decisions
WHERE tenant_id = :tenant_id
  AND incident_id = :incident_id
  AND action_fingerprint = :action_fingerprint
  AND decision = 'approved'
  AND expires_at > :now
ORDER BY expires_at DESC
LIMIT 1;

-- Correlated audit trace, bounded by tenant and correlation ID.
SELECT sequence_number, event_type, resource_type, resource_id, occurred_at
FROM audit_events
WHERE tenant_id = :tenant_id AND correlation_id = :correlation_id
ORDER BY sequence_number
LIMIT :limit;
