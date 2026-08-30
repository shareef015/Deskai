# Resume, replay, fork, and state migration

Resume reuses the authenticated tenant-owned thread and requires the exact incident, run, checkpoint digest, and configuration fingerprint. Replay and fork create new run and thread identities, preserve the source checkpoint unchanged, and append tenant-scoped provenance. Replay permits recorded tool results only; forks require new authorization before any side effect.

State versions advance through an explicit contiguous registry of pure upgrade functions. Every step has a reverse function, deep-copies input, preserves immutable tenant and incident scope, initializes new fields deterministically, and records migration provenance. Unknown versions, missing paths, downgrades, scope mutation, or invalid migrated state fail closed.

Replaying or forking before consent, approval, confirmation, or another pending interrupt deliberately clears the stale pending payload and requires a fresh human decision. Time travel uses the persisted checkpoint configuration and may create a branch through `update_state`; it never edits historical checkpoints.
