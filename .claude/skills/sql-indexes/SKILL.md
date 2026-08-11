---
name: sql-indexes
description: Database index design rules for PostgreSQL, MySQL and SQL Server — composite column ordering, leftmost prefix, covering and INCLUDE columns, cardinality anti-patterns, write and memory cost, and periodic auditing. Load before creating, changing or auditing an index, or when diagnosing a slow query.
---

# SQL index design

Read `AGENTS-sql.md` at the root of the agent-rules repo
(`../../../AGENTS-sql.md` relative to this skill) and apply it.

Start with `EXPLAIN` / `EXPLAIN ANALYZE` before proposing any index.
