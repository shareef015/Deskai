# PostgreSQL checkpoints and durable execution

DeskPilot compiles asynchronous graphs with LangGraph's production PostgreSQL checkpointer. Every execution supplies an opaque deterministic thread ID derived from tenant, incident, and run UUIDs; checkpoint namespaces remain available for specialist subgraphs. Native super-step checkpoints and pending writes support interrupts, resume, time travel, and recovery without rerunning successful parallel nodes.

Persisted channel values use LangGraph's encrypted serializer with an AES key resolved at runtime from the approved secret provider. Pickle fallback is prohibited. Checkpointer schema setup is an explicit deployment operation, never an application-start side effect.

A tenant-owned registry binds the opaque thread to its incident, run, state version, and exact configuration fingerprint. A row-level-secured checkpoint head provides optimistic concurrency, digest tracking, and bounded leases. Resume rejects tenant, incident, run, thread, or configuration mismatch. Cleanup applies only to expired terminal threads, excludes legal holds, and never deletes active or interrupted execution.
