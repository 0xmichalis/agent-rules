# Solidity Code Guidelines

Opinions and gotchas for Solidity. General style (descriptive names, early
exit, no redundant logic) is assumed — what follows is the part that isn't.

## Code Style

* Always use named import syntax; never import a whole file. As a repo
  grows and picks up dependencies with overlapping names, whole-file
  imports start producing duplicate-definition compiler errors.
* When writing an if/else, put the clause with most of the code in the
  `else` branch. Skip it when satisfying it would mean an empty block or a
  filler comment — that noise costs more than the ordering gains.

### Interfaces

Every contract MUST implement a corresponding interface covering all
externally callable functions, errors and events.

### NatSpec

The interface is the entrypoint for reading a contract, so it MUST carry
everything needed to understand the contract as NatSpec on its functions,
errors and events. A reader should never have to open the implementation to
learn what a function does.

* Implementations point back with `@inheritdoc`.
* Internal and private functions get no NatSpec beyond a `@dev` comment
  where extra context is genuinely needed.
* Comments inside a function body are for complex operations only.

## Security

* Follow CEI (checks-effects-interactions) wherever possible.
* Favor pull over push — make each user call in to withdraw their funds.
* Paginate `for` loops to avoid DOS.
* Use OpenZeppelin's
  [`SafeERC20`](https://docs.openzeppelin.com/contracts/5.x/api/token/erc20#SafeERC20)
  for every ERC20 interaction.
* External calls hand execution flow to a program that could do anything.
  Mark untrusted calls with a comment.
* Watch rounding direction — interest calculations get disastrous when it's
  wrong.

### Uniswap v4 pool initialization

Initializing a pool and seeding its liquidity in separate transactions
lets an attacker front-run the gap to set a manipulated `sqrtPriceX96`,
extract value from the initial LPs, or swap against the empty pool to move
the price first.

Bundle `initializePool()` and `modifyLiquidities()` through
`PositionManager.multicall()` — `PoolInitializer_v4` with `Multicall_v4` —
so both land atomically, and include slippage protection on the initial
liquidity.

Reference: OpenZeppelin Uniswap v4 Core Audit, Medium Severity —
["Front-Running Pool's Initialization or Initial Deposit Can Lead to
Draining Initial Liquidity"](https://www.openzeppelin.com/news/uniswap-v4-core-audit#medium-severity)

## Performance tricks

The assembly tricks below operate on **memory** only. Storage and calldata
have different representations, so reassigning a pointer across them is
not a cast — it's corruption.

* Bitmap nonces are cheaper than a naive `mapping(uint256 => bool)` for
  single-use / replay protection.
* Casting between compatible array types (`address[]` vs
  `address payable[]`, `address[]` vs `interface[]`, `uint160[]` vs
  `address[]`, `uint256[]` vs `bytes32[]`, `uint256[N]` vs `bytes32[N]`, …)
  doesn't need a new array and a copy loop — reassign the pointer with
  `assembly { newArr := oldArr }`. Same trick works for compatible structs.
  Only reassign when the layouts are identical and the target length is no
  greater than the source allocation.
* Shorten a dynamic memory array with `assembly { mstore(arr, newSize) }` —
  the length lives in the first memory slot. Shrinking only; growing reads
  memory that was never allocated for the array.
* Shorten a static memory array by creating one of the required size and
  doing `assembly { newArr := oldArr }`.

## Low level

Never bubble up revert data with `revert(string(revertBytes))` — that
re-encodes it as an `Error(string)` revert. Use
`assembly { revert(add(revertBytes, 0x20), mload(revertBytes)) }`.

## ERC20

If a contract needs to spend a user's ERC20 tokens, use
[EIP-2612](https://eips.ethereum.org/EIPS/eip-2612) so the user doesn't
have to send a separate `approve` first.

## Testing

* 100% coverage of functions, lines and branches on new code.
* Fuzz parameters and conditions whenever possible.
* Extremes go in dedicated edge case and corner case tests; invariants go
  in dedicated invariant tests.
* Use differential testing to compare an assembly implementation against a
  Solidity one, or against a non-Solidity reference via ffi.
* New features merge with their tests. A bug fix comes with a test that
  fails without the fix.

## Further Reading

Apply these on top of the above:

* [Solidity style guide](https://docs.soliditylang.org/en/latest/style-guide.html)
* [OpenZeppelin conventions](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/GUIDELINES.md#solidity-conventions)
