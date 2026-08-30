# Deterministic Termination

The graph cannot reason or loop indefinitely. Every transition passes through a deterministic guard with global step, reasoning-turn, phase-visit, identical-state, and no-progress limits. Only explicit lifecycle edges are permitted.

The guard fingerprints safety-relevant state rather than hidden model reasoning. Repeated fingerprints reveal cycles; repeated self-transitions without new evidence reveal stagnation. Budget exhaustion, invalid edges, cycles, stagnation, and weak evidence all terminate safely as human escalation. Terminal states are immutable.

Resolution remains possible only through the approved confirmation edge with sufficient evidence. Every terminal decision produces a proof containing the terminal state, reason, consumed budgets, final state fingerprint, and complete path digest. The proof is stored with the final state for audit and deterministic replay.
