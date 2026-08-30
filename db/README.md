# Database boundary

`schema.sql` is the authoritative logical PostgreSQL model. It uses composite
tenant keys to prevent cross-tenant references and keeps large evidence and AI
state in governed object storage through integrity-checked references.

Migration generation, repository transactions, query-plan tuning and enforced
row-level security are separate implementation boundaries. Application code
must never create tables dynamically or bypass the migration owner.
