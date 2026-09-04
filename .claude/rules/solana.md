---
paths:
  - "**/programs/**/*.rs"
  - "**/Anchor.toml"
---

# Solana Code Guidelines

Security rules and hard limits for Solana programs. This is a high-stakes
area, so it stays prescriptive — the constraints below are deliberate.

See [rust.md](./rust.md) for general Rust guidelines.

## Transaction limits

* Compute: each non-builtin instruction is allocated 200,000 CUs by default
  (builtins get 3,000). The transaction ceiling is 1,400,000 CUs, requested
  with `set_compute_unit_limit()`
  ([budget reference](https://solana.com/docs/core/fees/compute-budget))
* Transaction size: 1232 bytes. The increase to 4096 rides on the v1
  transaction format and is not active —
  [SIMD-0296](https://github.com/solana-foundation/solana-improvement-documents/pull/296)
  is still in review
* Account locks: `MAX_TX_ACCOUNT_LOCKS` is 128 per transaction
* CPI: the SDK's `MAX_CPI_ACCOUNT_INFOS` is 128, matching the lock limit.
  The runtime allows 255 with duplicates after
  [SIMD-0339](https://github.com/solana-foundation/solana-improvement-documents/pull/339),
  so budget against 128 unless you have checked the cluster

## Account Validation

* Verify ownership — `account.owner == expected_program`. Anchor's
  `Account<'info, T>` does this for accounts your program owns. For
  accounts from other programs (SPL Token, etc.) add the constraint
  yourself:
  `#[account(constraint = acc.to_account_info().owner == &expected_program::ID)]`
* Validate discriminators to prevent type cosplay, where an attacker
  substitutes a different account type with a matching data layout.
  `Account<'info, T>` and the `#[account]` macro handle this. Raw
  `AccountInfo<'info>` validates nothing — check ownership, data length and
  deserialization by hand.
* Assert the deserialized version matches the expected format.
* Assert global programs (e.g. SPL Token) are the real ones — use
  `Program<'info, T>`.
* Check `is_writable` matches what the instruction assumes.
* Validate data length before deserializing to prevent out-of-bounds reads.
* Enforce signers with `#[account(signer)]`, or check `is_signer` manually
  when using `AccountInfo`.
* When an instruction takes several accounts of the same type, constrain
  `user_a.key() != user_b.key()` so the same account can't be passed twice.
* Validate every input account, including read-only ones — reference-only
  accounts are still substitutable. In CPI scenarios validate the whole
  account chain to establish a root of trust.
* `UncheckedAccount` and `AccountInfo` bypass Anchor's validation entirely.
  Use them rarely, and document why validation is unnecessary in the
  `/// CHECK` comment Anchor requires.

## Anchor Constraints and Initialization

* Prefer `#[account(...)]` constraints over manual validation — enforced at
  the framework level, less boilerplate to get wrong.
* `#[account(has_one = ...)]` for relationship validation.
* `#[account(init)]` prevents reinitialization via the discriminator check
  and ensures rent exemption on creation.
* `#[account(init_if_needed)]` needs care — the state must be valid for
  both the new and the existing account.
* `#[account(zero)]` is not the same as proper initialization; the gap
  between them is exploitable.
* For manual creation, check
  `account.lamports() >= Rent::get()?.minimum_balance(account.data_len())`.
* Validate that a state transition is legal before mutating account data,
  and never mutate without an authorization check.

## Account Closing

Closing an account releases lamports and is good hygiene, but the data
survives until the end of the transaction — a later instruction referencing
the closed account has undefined behavior, and a credit of lamports in the
same transaction cancels the deletion.

The critical flaw: close an account, zero the data, then have a subsequent
instruction refund the rent, and the account survives with wiped data for
an attacker to re-initialize with their own. Anchor prevents this by
writing a special "closed" discriminator so all later deserializations
fail. Closing manually means sequencing it yourself or adding your own
discriminator check.

When deciding whether an account should be closed, check that both the data
and the lamports are non-zero.

## Account Design

* Isolate balances — never mix one user's funds with another's in the same
  account. A withdrawal-math bug then can't drain the whole pool.
* Prefer "gulping": move value between token accounts and mints instead of
  tracking it in bookkeeping variables. More expensive, but the token
  account is the source of truth.

## PDA Security

* Always re-derive and validate PDAs. Never accept a client-provided PDA.
* Use `#[account(seeds = [...], bump)]` for automatic validation.
* Store the bump in account data and verify with `bump = account.bump`
  (`create_program_address`) instead of re-running
  `find_program_address`, which has to search for it — the compute saving
  is significant.
* When deriving manually, use the canonical bump from
  `find_program_address`; non-canonical bumps yield multiple valid PDAs for
  the same seeds.
* Seeds must be deterministic and not user-manipulable.
* Prevent PDA sharing — include the user pubkey (or equivalent) in the
  seeds so each user gets a distinct PDA. Program-controlled, user-specific
  vaults must never share a PDA authority across authority domains.
* Use `has_one` to validate PDA relationships with other accounts.

## CPI Security

* Validate program IDs with `Program<'info, T>`. Never pass an arbitrary
  program account into a CPI — an attacker can substitute a malicious one.
* Validate ownership of accounts coming from other programs; this matters
  most in CPI.
* With `invoke_signed`, make sure signer seeds are correct and not
  manipulable.
* The callee can call back into your program. Design state machines that
  prevent reentrancy, or re-validate state consistency after the CPI
  returns.
* When chaining delegations of signature verification, validate every step
  of the chain rather than trusting an intermediate result.

## Arithmetic

* Set `overflow-checks = true` on the release profile. Cargo disables it by
  default, and programs ship in release mode, so `a + b` wraps silently.
* Even with that set, use `checked_add`, `checked_sub`, `checked_mul`,
  `checked_div`, `checked_pow` for user-controlled or critical values so
  the overflow becomes an error you handle rather than a panic. Handle the
  `Option`; never unwrap it.
* Avoid `saturating_*` for critical calculations — silently clamping on
  overflow produces wrong numbers rather than an error.
* Prefer `try_floor_u64()` over `try_round_u64()` when converting decimals;
  rounding accumulates precision loss that enables arbitrage. When in
  doubt, floor or ceil deliberately — never round.

## Testing

Beyond the usual unit and `solana-program-test` integration coverage, test
the attacks:

* Invalid signers
* Incorrect PDA derivations
* Arithmetic overflow/underflow
* Invalid account ownership and missing validations
* Duplicate mutable accounts
* Type cosplay (wrong account types)
* Reinitialization attempts
* Arbitrary CPI with malicious programs
* Rent exemption edge cases
* `UncheckedAccount` / `AccountInfo` validation bypasses
* Signature delegation chaining
* Oracle manipulation
* Semantic inconsistency
* Reentrancy through CPI
* Zero initialization
* Substitution of unmodified, reference-only accounts

## Further Reading

* [Sealevel Attacks](https://github.com/coral-xyz/sealevel-attacks) - Common
  security exploits and protections on Solana
* [Solana Security Best Practices](https://solana.com/developers/guides) -
  Official Solana developer guides
* [Anchor Documentation](https://www.anchor-lang.com/) - Anchor framework
  documentation and security patterns
