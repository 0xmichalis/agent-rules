# SQL Index Design Rules

Guidelines for designing and maintaining database indexes. Apply these rules
when creating, modifying, or auditing indexes in PostgreSQL, MySQL, or SQL Server.

## Index Design Rules

* Always check the query plan first — run EXPLAIN / EXPLAIN ANALYZE before
  reaching for CREATE INDEX. Identify whether the bottleneck is a full table
  scan, excessive bookmark lookups, or an on-disk sort.
* Equality columns first, range columns last in composite indexes. Equality
  filters let the B-tree jump to a precise group; range filters (>, <, BETWEEN)
  start a leaf scan that trailing columns can't narrow.
* Column order is the design decision — the same columns in a different order
  produce an entirely different index serving entirely different queries. Match
  the leading columns to what your queries actually filter on.
* Respect the leftmost prefix rule — a composite index on (A, B, C) is usable
  for queries filtering on A, A+B, or A+B+C. Skipping A renders the index
  largely useless (skip scan is a fallback, not a strategy).
* Don't skip columns in a composite index and expect full efficiency —
  filtering on A and C but skipping B means the index finds all of A's rows,
  then filters C the hard way within that set. Partial use, not full use.
* Use covering indexes for high-frequency queries — include all columns the
  query needs (SELECT, WHERE, ORDER BY, GROUP BY) so the database never touches
  the main table. Look for Index Only Scan (Postgres), Using index (MySQL), or
  absence of Key Lookup (SQL Server) in the plan.
* Use INCLUDE columns instead of widening the sort key — Postgres and SQL
  Server let you attach payload columns to leaf nodes without changing the
  B-tree's sort structure. Cover the query without redesigning the index.
* Don't over-widen covering indexes — a covering index with 8+ columns doubles
  the index size on disk and in memory. Only worth it for specific
  high-frequency queries, not as a general policy.

## Anti-Pattern Rules

* Don't index low-cardinality columns on their own with even distribution — a
  status column with 3 values still points to ~33% of the table, and random
  lookups from that are often worse than a sequential scan.
* Low cardinality with skewed distribution is fine — if 98% of rows are active
  and 1% are pending, the index is efficient for queries targeting pending.
  Consider a partial index covering only the rare value.
* Don't add speculative indexes — indexes added "just in case" accumulate write
  cost silently with no read benefit.
* Every index is a write cost — each insert writes to every index on the table.
  A table with 12 indexes means 13 writes per insert. Updates to indexed
  columns require a remove + re-insert. Deletes clean up every index.
* Be aware of the memory cost — indexes compete for the buffer pool. Too many
  indexes mean each gets a smaller share of RAM, causing disk reads — the
  exact problem you were trying to solve.
* The query planner may ignore your index — if the query returns a large
  fraction of the table (~10–30%+), random lookups from the index cost more
  than a sequential scan. The tipping point depends on row width and storage
  type (SSD vs spinning disk).

## Maintenance Rules

* Audit indexes periodically — use pg_stat_user_indexes (Postgres),
  sys.schema_unused_indexes (MySQL), or sys.dm_db_index_usage_stats (SQL
  Server) to find indexes with zero scans. Drop what isn't earning its keep.
* Revisit indexes when queries change — features get removed, reports stop
  running, but their indexes remain, silently costing on every write.
* Evaluate the write side before shipping a new index — if the table gets
  hundreds of inserts per second, make sure the read improvement justifies the
  ongoing write overhead.
