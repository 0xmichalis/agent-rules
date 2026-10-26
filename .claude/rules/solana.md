---
paths:
  - "**/programs/**/*.rs"
  - "**/Anchor.toml"
---

# Solana programs

* Verify limits and feature activation against the target cluster and pinned
  SDK. Don't encode remembered transaction sizes, CU limits or CPI limits as
  permanent assumptions.
* Establish account ownership, type/version, signer authority, writable status
  and relationships before mutation. Typed Anchor wrappers perform some of
  these checks; inspect their actual guarantees instead of duplicating them or
  assuming unchecked accounts are validated.
* Validate read-only reference accounts too. Reject aliasing when accounts must
  be distinct. Document the concrete validation behind every `CHECK` comment.
* Prefer framework constraints for initialization, ownership, relationships and
  PDA seeds. Derive canonical bumps during initialization and validate stored
  bumps thereafter. Bind authority domains explicitly; never trust a supplied
  address or bump without validation.
* Authorize state transitions. Test initialization and reinitialization paths,
  including `init_if_needed`. Verify close/revival behavior against the pinned
  Anchor implementation; avoid relying on a historical discriminator mechanism.
* Validate CPI program IDs and the authority granted by signer seeds. Respect
  the target runtime's call restrictions and revalidate affected state when
  necessary after external execution.
* Use checked arithmetic for critical values and handle errors explicitly.
  Enable overflow checks in deployment profiles. Choose rounding direction from
  the economic invariant; silent saturation and unconditional flooring can both
  be wrong.
* Test hostile accounts, missing signers, substitution, duplicate mutable
  accounts, reinitialization, malformed layouts, arithmetic boundaries, oracle
  manipulation and invalid state transitions. Prove the authorization and value
  conservation properties, not only the happy path.

References: [Anchor](https://www.anchor-lang.com/docs),
[account wrappers](https://www.anchor-lang.com/docs/references/account-types),
[Sealevel attacks](https://github.com/coral-xyz/sealevel-attacks).
