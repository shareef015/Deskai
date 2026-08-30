# Connected staging connected-staging evidence schema

Every blocking control requires a real staging evidence record. Do not mark a control PASS from synthetic fixtures.

```json
{
  "control_id": "postgres_rls",
  "status": "pass",
  "source": "staging/postgres/rls-probe-20260827.json",
  "observed_at": "2026-08-27T14:00:00Z",
  "fingerprint": "sha256-of-immutable-evidence",
  "environment": "staging",
  "notes": ["tenant-a cannot read or write tenant-b rows"]
}
```

`status` is one of `pass`, `fail`, or `not_run`. `source`, `observed_at`, `fingerprint`, and `environment=staging` are mandatory for any evidence used to pass the RC gate.
