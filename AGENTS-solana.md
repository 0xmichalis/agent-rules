# Solana Code Guidelines

Guidelines specific to Solana blockchain development in Rust.

## General Rust Guidelines

For comprehensive Rust best practices, refer to [AGENTS-rust.md](./AGENTS-rust.md).

## General Practices

* Use `anchor` framework conventions when working with Anchor programs
* Use `Pubkey` type from `solana_program` for public keys
* Follow Solana's account ownership model - programs own accounts they create
* Use `SystemProgram` for creating accounts when appropriate
* Understand Solana transaction limits:
  * Compute limit: 200k compute units per transaction (default), up to 1.4M
    maximum using `set_compute_unit_limit()` ([source](https://solana.com/developers/guides/advanced/how-to-optimize-compute))
  * Transaction size limit: 1232 bytes (to be increased to 4096 bytes with
    [SIMD-0296](https://github.com/solana-foundation/solana-improvement-documents/pull/296))
  * Accounts limit: 128 unique accounts per transaction (transaction's account
    array). CPI account info limit: 255 AccountInfo structs per CPI call (can
    reference same accounts multiple times, allowing duplicates) with
    [SIMD-0339](https://github.com/solana-foundation/solana-improvement-documents/pull/339)

## Security Best Practices

### Account Validation

* Always verify account ownership - check `account.owner == expected_program`.
  Anchor's `Account<'info, T>` wrapper automatically validates ownership for
  accounts owned by your program. When using accounts from other programs (e.g.,
  SPL Token accounts), manually validate ownership with a constraint:
  `#[account(constraint = acc.to_account_info().owner == &expected_program::ID)]`
* Validate account discriminators to prevent type cosplay attacks where attacker
  substitutes different account types with matching data layouts:
  * Use Anchor's `Account<'info, T>` wrapper which automatically validates
    discriminators and ownership
  * Use `#[account]` macro on account structs for automatic discriminator
    validation
  * When using raw `AccountInfo<'info>` (for non-Anchor accounts like SPL
    tokens, system accounts), manually validate ownership, data length, and
    deserialize correctly - `AccountInfo` provides no automatic validation
* Check that data is deserialized correctly - assert version matches expected
  format
* Assert global programs are correct (e.g., SPL Token program) when
  interacting with them - use `Program<'info, T>` wrapper in Anchor
* Verify account mutability matches expectations - check `is_writable` flag
* Validate account data length before deserialization to prevent out-of-bounds
  access
* Always verify signer requirements:
  * Use Anchor's `#[account(signer)]` constraint to enforce signer requirements
  * When using `AccountInfo`, manually check `is_signer` flag for accounts
    that must sign transactions
* Prevent duplicate mutable accounts - when instruction takes multiple
  accounts of same type, add constraint `user_a.key() != user_b.key()` to
  prevent same account being passed twice
* Never trust account data without validation - validate before use
* Always validate all input accounts - never accept accounts without proper
  validation, especially in CPI scenarios. Establish a root of trust by
  validating the entire account chain
* When using `UncheckedAccount`, always document why validation is not needed
  with `/// CHECK` comments - Anchor requires this documentation. Be extremely
  cautious with `UncheckedAccount` and `AccountInfo` as they bypass Anchor's
  automatic validation
* Validate unmodified, reference-only accounts - even accounts that are only
  read and not modified must be validated to prevent substitution attacks

### Anchor Constraints and Account Initialization

* Prefer Anchor constraints (`#[account(...)]`) over manual validation when
  possible - they're enforced at the framework level and reduce boilerplate
* Use `#[account(has_one = ...)]` for account relationship validation
* Use `#[account(init)]` which prevents reinitialization attacks - the
  discriminator check ensures already-initialized accounts cannot be
  reinitialized. Automatically ensures rent exemption during account creation
* Use `#[account(init_if_needed)]` with caution - ensure the account state
  is valid for both new and existing accounts
* Be careful with zero initialization patterns - ensure proper initialization
  of account data. The difference between `#[account(zero)]` and proper
  initialization can lead to vulnerabilities if not handled correctly
* For manual account creation, ensure rent exemption by checking
  `account.lamports() >= Rent::get()?.minimum_balance(account.data_len())`
* Validate account state transitions are valid before mutating account data
* Never mutate account data without proper authorization checks

### Account Closing

* Use caution when closing accounts - closing releases lamports and is good
  hygiene. Account data remains until end of transaction - subsequent instructions
  referencing the soon-to-be-deleted account can have undefined behavior. An
  account could be credited with more lamports during the same transaction,
  cancelling the deletion
* When checking if an account should be closed, verify both that data is
  non-zero and lamports is non-zero
* Critical flaw: If you close an account, zero the data, and a subsequent
  instruction refunds the rent, the account remains with wiped data - an
  attacker can re-initialize the same account with different data. Anchor
  automatically prevents this by replacing the account discriminator with a
  special "is closed" discriminator, causing all subsequent deserializations
  to fail. For manual account closing, ensure proper sequencing or use
  discriminator checks to prevent reinitialization.

### Account Design

* Implement balance isolation when possible - never mix funds belonging to one
  user with funds belonging to another user in the same account. If there's a
  bug in calculating withdrawals, it's less likely to affect the entire pool
  deposit
* Use "gulping" pattern when possible - instead of tracking balances with
  separate bookkeeping variables, use token accounts and mints to transfer back
  and forth between vaults. It's more expensive but more robust - the token
  account is the source of truth

### PDA (Program Derived Address) Security

* Always re-derive and validate PDAs - never accept client-provided PDAs
  without verification
* Use Anchor's `#[account(seeds = [...], bump)]` constraints for automatic
  PDA validation
* Store bump seed in account data and use `bump = account.bump` for efficient
  verification in subsequent instructions - this significantly reduces compute
  usage compared to using `find_program_address` which must search for the bump
  (use `create_program_address` with stored bump instead)
* When deriving manually, use canonical bump from `find_program_address` -
  non-canonical bumps can lead to multiple valid PDAs for same seeds
* Ensure PDA seeds are deterministic and cannot be manipulated by users
* Prevent PDA sharing attacks - use unique seeds per user/context (e.g.,
  include user pubkey in seeds) to ensure each user gets distinct PDA. Common
  issue: program-controlled, user-specific vaults holding deposits must have
  PDA authority unique to that user - never share PDAs across authority domains
* Verify PDA derivation matches expected seeds in all cases
* Use `has_one` constraints to validate PDA relationships with other accounts

### Cross-Program Invocation (CPI) Security

* Always validate program IDs when doing CPI - use Anchor's `Program<'info, T>`
  wrapper which validates the program ID automatically
* Always validate account ownership when using accounts from other programs in
  CPI - this is especially critical in CPI scenarios (see Account Validation
  section for details)
* Never pass arbitrary program accounts to CPI without validation - attacker
  could substitute with a malicious program
* When using `invoke_signed`, ensure signer seeds are correct and cannot be
  manipulated
* Validate all accounts passed to CPI are the expected accounts
* Be aware of reentrancy risks - external program could call back into your
  program during CPI. Consider state machine design that prevents reentrancy
  or validates state consistency after CPI calls
* When chaining delegations of signature verifications, ensure the chain
  leads to proper verification - validate each step in the delegation chain
* Establish a root of trust - validate the entire chain of accounts and
  programs from a trusted source rather than accepting intermediate results
  without verification

### Arithmetic Operations

* Always use checked arithmetic for user-controlled or critical values - be
  aware of integer overflow bugs in Solana rBPF:
  * Use `checked_add()`, `checked_sub()`, `checked_mul()`, `checked_div()`,
    `checked_pow()` instead of `+`, `-`, `*`, `/`, `pow()`
  * Handle `Option` results with proper error handling - never unwrap
* Avoid `saturating_*` methods for critical calculations - they silently
  saturate on overflow/underflow leading to incorrect results
* Use `try_floor_u64()` instead of `try_round_u64()` when converting decimals
  to prevent precision loss that can enable arbitrage attacks. Rounding errors
  can accumulate and lead to significant vulnerabilities - when in doubt, use
  `floor` (or `ceil` depending on direction) instead of `round`

### Error Handling

* Return appropriate `ProgramError` types for security violations - never
  silently fail
* Use Anchor's error types (`AnchorError`) when working with Anchor programs
* Provide clear error messages for debugging

## Testing

* Write unit tests for program logic
* Use `solana-program-test` for integration testing
* Mock accounts and programs appropriately in tests
* Test security edge cases:
  * Invalid signers
  * Incorrect PDA derivations
  * Arithmetic overflow/underflow scenarios
  * Invalid account ownership
  * Missing account validations
  * Duplicate mutable accounts
  * Type cosplay attempts (wrong account types)
  * Reinitialization attempts
  * Arbitrary CPI with malicious programs
  * Rent exemptions
  * UncheckedAccount and AccountInfo validation bypasses
  * Signature delegation chaining attacks
  * Oracle manipulation scenarios
  * Semantic inconsistency vulnerabilities
  * Reentrancy through CPI
  * Zero initialization edge cases
  * Unmodified reference-only account substitution
* Test with malicious inputs and edge cases
* Verify all constraints are properly enforced in tests

## Further Reading

* [Sealevel Attacks](https://github.com/coral-xyz/sealevel-attacks) - Common
  security exploits and protections on Solana
* [Solana Security Best Practices](https://solana.com/developers/guides) -
  Official Solana developer guides
* [Anchor Documentation](https://www.anchor-lang.com/) - Anchor framework
  documentation and security patterns
