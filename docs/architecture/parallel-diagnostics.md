# Parallel Diagnostics and Evidence Reduction

When routing identifies two plausible domains, the supervisor may fan out to at most two read-only specialist subgraphs. Branches run concurrently with independent timeouts. One failed or timed-out branch does not discard safe evidence from another, while parent cancellation cancels and awaits every child task.

Convergence is deterministic. Results are ordered by domain; evidence is scope-checked, raw content is rejected, identical digests are deduplicated, and stable evidence ordering is applied. Different digests for the same source and evidence kind are retained and explicitly marked as contradictions rather than overwritten.

All failed branches escalate. Partial evidence proceeds to evidence fusion when useful, otherwise clarification. Contradictions always proceed to evidence fusion for critic review. Branch statuses, evidence identifiers, contradictions, convergence route, and a deterministic fingerprint are returned to the supervisor for audit and replay.
