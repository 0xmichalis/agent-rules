---
paths:
  - "**/*.sol"
---

# Solidity

* Use named imports and follow the repository's interface conventions. Put the
  external contract's NatSpec on its interface and use `@inheritdoc`; reserve
  implementation comments for non-obvious invariants.
* Authorize changes before external interaction. Follow checks-effects-
  interactions where applicable, bound work over growing collections, and use
  SafeERC20 for compatible ERC20 transfers. Make trust boundaries explicit.
* Support permit where the token and signer support it; retain an approval-based
  path for tokens and contract wallets that cannot use ERC-2612. Handle the
  relevant front-running and replay cases.
* Choose rounding direction from the value-conservation invariant. Test zero,
  boundary, extreme and adversarial inputs rather than chasing a coverage number.
* When initializing Uniswap v4 liquidity, use a supported atomic initialization
  and initial-liquidity path with slippage protection. Verify the actual deployed
  periphery interfaces rather than assuming one helper exists everywhere.
* Use assembly only for a demonstrated need. Prove memory layout and bounds;
  don't reinterpret storage/calldata as memory or grow beyond an allocation.
  Preserve raw revert data when bubbling errors.
* Add regression tests for bugs, fuzz relevant inputs, test invariants, and
  compare optimized or assembly paths against a straightforward reference.

References: [OpenZeppelin ERC20 and permit](https://docs.openzeppelin.com/contracts/5.x/api/token/erc20),
[Solidity conventions](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/GUIDELINES.md#solidity-conventions).
