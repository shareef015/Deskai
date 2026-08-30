# Query-plan verification

Load representative, skewed synthetic tenant data before capturing plans. For
each statement in `critical-queries.sql`, execute `EXPLAIN (ANALYZE, BUFFERS,
WAL, FORMAT JSON)` with realistic bindings and retain the JSON plan as a CI
artifact. Never use `ANALYZE` against an unbounded production mutation.

Fail the performance gate when a tenant query lacks a tenant-leading index,
performs an unbounded sequential scan, spills an interactive sort/hash to disk,
or exceeds the estimated-to-actual row ratio or latency contract. Plan shapes
are advisory across PostgreSQL upgrades; behavioral thresholds are authoritative.
