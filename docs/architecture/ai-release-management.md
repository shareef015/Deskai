# Prompt, Agent and Model Release Management

An AI release is one immutable bundle binding exact prompt, agent-policy, model-profile, graph and schema versions to an approved evaluation run. Every declared compatibility edge must pass before review.

Authors cannot approve their own bundles. Qualified release managers assign approved bundles to synthetic, staging or production deployments through bounded canaries; environment assignments remain separate.

Promotion and rollback append deployment events with hashed actors and prior-bundle provenance. Emergency controllers can freeze an environment immediately, blocking all further rollout until governed human recovery.
