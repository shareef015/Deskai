# Prompt and Agent Configuration Registry

Prompts and agent configurations are immutable, content-addressed artifacts. Prompt templates declare exact variables and input/output schema versions. Agent configurations bind one prompt digest to state and I/O schema versions, a sorted tool allowlist, and bounded step, tool, and token budgets.

Authors cannot approve their own artifacts. A release bundle requires independent approval for both prompt and agent configuration plus versioned evaluation evidence meeting groundedness, task-success, safety, and regression gates. The tenant, artifact digests, and evaluation report produce the exact runtime configuration fingerprint.

Deployment changes a tenant-scoped active pointer through append-only canary, activation, or rollback events. Canary exposure is capped. Rollback targets an existing fingerprint and never edits historical artifacts. The model cannot self-modify configuration, silently substitute an artifact, activate an unapproved release, or embed secret-like values in prompts.
