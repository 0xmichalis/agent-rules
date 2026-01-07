# Rust Code Guidelines

Guidelines for Rust development. Most of these rules are based on
[Canonical's Rust Best Practices](https://canonical.github.io/rust-best-practices/).

## Cosmetic Discipline

* Use blank lines semantically, rather than aesthetically. They should be used
  consistently, regardless of the size of a section of code, to delimit strongly
  associated sections. There are no hard and fast rules for this strong association,
  but the following heuristics are quite effective:
  * If a variable is declared and only used in the block of code which follows it,
    that declaration and block are strongly associated. Do not put a blank line
    here.
  * If a variable is used in multiple blocks of code, not just the one which
    follows it, that declaration is not strongly associated with the block
    immediately after it. Put a blank line here.
  * If a variable is declared and then checked, the declaration and check are
    strongly associated and must not be separated by a blank line. If the check
    contains more than three lines, the declaration and check start to form their
    own strongly associated block so require a blank line after.
* Don't interleave unrelated code. Remember, to a new reader, this will look
  deliberate and they become confused about how variables relate. Keep it clean
  and group together strongly intradependent sections of code. This is
  particularly significant where closures are bound to variables—if a closure is
  defined as such halfway through a function, does not capture anything and
  then is only used at the end, the reader will have to keep more things in
  mind for no good reason. If values are captured, declare such closures close
  as possible to where they're needed. Otherwise, define an fn function, rather
  than a closure with || .... Also, consider whether a closure is required at
  all—although it may be tempting to define helper closures, code may feel
  cleaner with a simpler, more top-to-bottom flow control pattern. Logic should
  always feel clean and be easy to follow.
* When writing conditional statements (if-else, match arms, etc.), always place
  the shortest clause first to enhance readability. This applies to both simple
  conditions and complex nested logic. For example, prefer
  `if condition.is_none() { short_clause } else { long_clause }` over
  `if let Some(value) = condition { long_clause } else { short_clause }`.
  Avoid adding empty blocks or meaningless comments just to satisfy this rule;
  only apply it when it genuinely improves readability without introducing noise.

## Naming Discipline

* Follow Rust naming conventions:
  * `snake_case` for functions, variables, and modules
  * `PascalCase` for types, traits, and enum variants
  * `SCREAMING_SNAKE_CASE` for constants and static variables
* Use descriptive names that convey intent, not implementation details
* Avoid abbreviations unless they are widely understood (e.g., `id`, `num`,
  `idx`)
* Prefer verb phrases for functions (`get_user`, `calculate_total`) and noun
  phrases for types (`User`, `Total`)
* Use type aliases to improve readability when dealing with complex types

## Import Discipline

* Group imports logically: standard library, external crates, internal modules
* Order imports alphabetically within each group
* Avoid wildcard imports (`use module::*`) except in specific cases like test
  modules
* Use absolute paths for clarity when importing from external crates
* Keep `use` statements at the top of the file, after module-level
  documentation
* Use `pub use` sparingly and only when re-exporting is necessary for the
  public API

## Pattern Matching Discipline

* Always handle all possible cases in `match` statements—be exhaustive
* Use `_` placeholder only when you genuinely don't care about the value
* Prefer explicit pattern matching over `if let` when multiple cases need
  handling
* Use pattern matching in function parameters when destructuring improves
  clarity
* Avoid deep nesting in pattern matches—consider extracting to helper
  functions
* Use guards (`if` conditions in match arms) to add additional constraints
  when needed
* Prefer `match` over multiple `if-else` chains for better exhaustiveness
  checking

## Code Discipline

* Keep functions focused on a single responsibility
* Prefer composition over complex nested logic
* Use early returns to reduce nesting and improve readability
* Extract magic numbers and strings into named constants
* Prefer `&str` over `String` for function parameters when ownership isn't needed
* Use `Cow<'_, str>` when you need flexibility between borrowed and owned
  strings
* Avoid unnecessary cloning—use references (`&`) when possible
* Use iterator methods (`map`, `filter`, `fold`, etc.) instead of manual loops
  when appropriate
* Prefer `Option` and `Result` types over `null`-like patterns

## Error and Panic Discipline

* Use `Result<T, E>` for recoverable errors, never panic for expected error conditions
* Avoid `unwrap()` and `expect()` in production code—use proper error handling
* Use `unwrap()` only in tests or when you're certain the value exists
* Prefer the `?` operator for error propagation over manual `match` statements
* Create custom error types using `thiserror` or `anyhow` for better error context
* Use `panic!` only for programming errors (bugs), not for runtime errors
* Document panicking conditions in function documentation when they exist
* Consider using `Option` for cases where "not found" is a valid, expected state

## Function Discipline

* Keep functions short and focused—if a function exceeds ~50 lines, consider
  refactoring
* Limit function parameters to 3-4; use structs or builder patterns for more
  complex inputs
* Prefer returning `Result` or `Option` over using out parameters
* Use `#[must_use]` attribute for functions where ignoring the return value
  is likely a bug
* Document public functions with `///` doc comments explaining purpose,
  parameters, and return values
* Group related functions together in modules
* Use function overloading patterns (traits, generics) when appropriate, but
  don't over-engineer

## Ordering Discipline

* Order items in modules consistently:
  1. Module-level documentation
  2. `use` statements
  3. Constants and statics
  4. Type definitions (structs, enums, type aliases)
  5. Traits and implementations
  6. Public functions
  7. Private helper functions
* Place public items before private ones
* Group related items together (e.g., all methods for a struct)
* Order trait implementations consistently (e.g., alphabetically by trait name)
* Keep related code close together—don't scatter related functionality across files

## Unsafe Discipline

* Minimize use of `unsafe` code—only use when absolutely necessary
* Encapsulate `unsafe` code in safe abstractions with clear safety invariants
* Document all `unsafe` blocks with comments explaining why it's safe
* Document the safety invariants that must be maintained
* Prefer using well-tested `unsafe` abstractions from the standard library or crates
* Never use `unsafe` to work around borrow checker limitations without
  understanding the implications
* Consider using `#![deny(unsafe_code)]` at the crate level if unsafe isn't needed
* Review all `unsafe` code carefully—it's easy to introduce undefined behavior

## Structural Discipline

* Use modules to organize code logically—don't put everything in one file
* Keep related functionality together in the same module
* Use `mod.rs` or `lib.rs`/`main.rs` to organize submodules
* Prefer small, focused modules over large, monolithic ones
* Use `pub` visibility judiciously—keep implementation details private
* Consider using `pub(crate)` for items that should be visible within the crate
  but not externally
* Use `cfg` attributes to conditionally compile code for different targets
* Structure tests in a `tests/` directory for integration tests, `#[cfg(test)]`
  modules for unit tests

## Comment Discipline

* Use `///` for public API documentation—these appear in generated docs
* Use `//` for inline comments explaining non-obvious code
* Write documentation comments for all public items (functions, types, modules)
* Include examples in documentation when they clarify usage
* Keep comments up-to-date with code changes
* Don't comment obvious code—let the code speak for itself
* Use comments to explain "why" not "what"—the code should be self-explanatory
* Mark `TODO`, `FIXME`, and `NOTE` comments clearly if they must remain
* Use `#[doc(hidden)]` for items that are public but not part of the intended API

## SQL Best Practices

* **sqlx**: Use `sqlx::query_as!` to validate queries at compile time. Parameterize
  inputs with numbered parameters (e.g., `$1`, `$2`) to avoid SQL injection.
* **Diesel**: Use Diesel's query builder API for compile-time query validation.
  For raw SQL, use `diesel::sql_query` with `.bind()` for parameters (e.g., `$1`,
  `$2` for PostgreSQL, `?` for SQLite) to avoid SQL injection.
* Define reusable query constants with descriptive names at module scope.
* Map database errors to appropriate HTTP status codes and log details for debugging.
* Use transactions for multi-table operations that must stay consistent.

## Further Reading

* [Canonical's Rust Best Practices](https://canonical.github.io/rust-best-practices/)
  * The source for these guidelines
* [The Rust Book](https://doc.rust-lang.org/book/) - Comprehensive Rust
  language guide
* [Rust for Rustaceans](https://rust-for-rustaceans.com/) - Advanced Rust
  patterns and practices
* [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/) - API
  design guidelines
