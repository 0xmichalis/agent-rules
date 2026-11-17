---
paths:
  - "**/*.rs"
---

# Rust

* Follow local import and formatting conventions; prefer imports over repeated
  fully qualified paths. Let rustfmt and clippy enforce mechanical style.
* Group related operations. Put capturing closures near their use; prefer a
  named function when no capture is needed. Blank lines separate logical groups.
* Prefer the shorter conditional arm first when it improves readability, without
  empty branches or filler comments.
* Explain an intentional `#[allow(dead_code)]`; don't add it to hide code your
  own change made obsolete.
* Parameterize SQL and keep dependent writes transactional. Follow the repo's
  choice of checked macros or runtime queries; regenerate offline caches only
  against a dedicated local database with committed migrations.
* Match assertions to the contract: exact values for exact behavior, justified
  tolerances for approximate numerical results.

Derived in part from
[Canonical's Rust Best Practices](https://canonical.github.io/rust-best-practices/)
and licensed under GPL v3.0 as documented in the repository README.
