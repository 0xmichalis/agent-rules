# Rust Code Guidelines

Opinions and gotchas for Rust work. Naming conventions, import ordering,
`match` exhaustiveness, `?` over manual propagation and the rest of the
basics are deliberately absent — `rustc`, `rustfmt` and `clippy` already
enforce those, so run them instead of reading about them here.

Most of these rules are based on
[Canonical's Rust Best Practices](https://canonical.github.io/rust-best-practices/).

## Blank lines carry meaning

Use blank lines semantically rather than aesthetically: they delimit
strongly associated sections, and they do so consistently regardless of how
big a section is.

* A variable declared and used only by the block that follows it is
  strongly associated with that block — no blank line between them.
* A variable used by several later blocks is not associated with the one
  immediately after it — put a blank line.
* A declaration and the check that guards it belong together — no blank
  line. Once that check runs past ~3 lines the pair has become its own
  block, so put a blank line after it.

## Don't interleave unrelated code

To a new reader, interleaving looks deliberate and they'll go hunting for a
relationship that isn't there. Group strongly intradependent sections.

This bites hardest with closures. A closure bound to a variable halfway
through a function, capturing nothing, used only at the end, forces the
reader to carry it the whole way. If it captures, declare it next to where
it's needed; if it doesn't, make it an `fn`. Often it shouldn't be a
closure at all — a top-to-bottom flow reads better than a helper closure.

## Shortest clause first

In conditionals and match arms, put the shorter clause first:
`if condition.is_none() { short } else { long }` reads better than
`if let Some(value) = condition { long } else { short }`.

Skip it when satisfying it would mean an empty block or a filler comment —
that noise costs more than the ordering gains.

## Dead code

`#[allow(dead_code)]` always carries a comment explaining why the code is
being kept rather than deleted.

## SQL

* **sqlx**: `sqlx::query_as!` validates queries against the database at
  compile time. Parameterize with `$1`, `$2`, … — never interpolate.
* **Diesel**: prefer the query builder for compile-time validation. For raw
  SQL use `diesel::sql_query` with `.bind()` (`$1`/`$2` on PostgreSQL, `?`
  on SQLite).
* Define reusable query constants with descriptive names at module scope.
* Multi-table writes that must stay consistent belong in a transaction.
* Map database errors onto HTTP status codes and log the underlying detail.

See [AGENTS-sql.md](./AGENTS-sql.md) before adding or changing an index.

## Further Reading

* [Canonical's Rust Best Practices](https://canonical.github.io/rust-best-practices/)
  * The source for these guidelines
* [The Rust Book](https://doc.rust-lang.org/book/) - Comprehensive Rust
  language guide
* [Rust for Rustaceans](https://rust-for-rustaceans.com/) - Advanced Rust
  patterns and practices
* [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/) - API
  design guidelines
