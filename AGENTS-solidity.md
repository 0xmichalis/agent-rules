# Solidity Code Guidelines

Guidelines specific to blockchain development in Solidity.

## Code Style

* Always use named import syntax, don’t import full files. This restricts
  what is being imported to just the named items, not everything in the
  file. Importing full files can result in compiler errors about
  duplicate definitions, especially as repos grow and have more
  dependencies with overlapping names.
* Use descriptive variable names.
* Limit the number of active variables.
* No redundant logic.
* Related code should be placed near each other.
* Exit early and avoid nested code as much as possible to reduce mental
  load for code reviewers.
* When writing an if/else clause, prefer putting the clause with most of
  the code in the else part to keep the whole conditional more readable.
  Avoid adding empty blocks or meaningless comments just to satisfy this rule;
  only apply it when it genuinely improves readability without introducing noise.

### Interfaces

Every contract MUST implement their corresponding interface that includes
all externally callable functions, errors and events.

### NatSpec & Comments

Interfaces should be the entrypoint for all contracts. When exploring a
contract within the repository, the interface MUST contain all relevant
information to understand the functionality of the contract in the form
of NatSpec comments. This includes all externally callable functions,
errors and events. The NatSpec documentation MUST be added to the
functions, errors and events within the interface. This allows a reader
to understand the functionality of a function before moving on to the
implementation. The implementing functions MUST point to the NatSpec
documentation in the interface using `@inheritdoc`. Internal and private
functions shouldn't have NatSpec documentation except for `@dev`
comments, whenever more context is needed. Additional comments within a
function should only be used to give more context to more complex
operations, otherwise the code should be kept readable and
self-explanatory.

## Security

* Follow CEI pattern (checks-effects-interactions) whenever possible.
* Favor pull over push model, eg. when withdrawing funds, make each user
  call the contract to withdraw their funds.
* Paginate `for` loops to avoid DOS issues.
* When interacting with ERC20 tokens, always use OpenZeppelin's
  [`SafeERC20`](https://docs.openzeppelin.com/contracts/5.x/api/token/erc20#SafeERC20)
  library.
* Use caution when making external calls. This gives execution flow to external
  program which could do anything. Mark untrusted calls with comments.
* Use caution when rounding, eg, interest calculations can be disasterous
  when done incorrectly.

## Performance tricks

* When implementing nonces to guarantee single use and avoid replay
  attacks, use bitmap nonces instead of a naive `mapping (uint256 =>
  bool)` as the gas cost for bitmaps tends to be cheaper.
* When casting between array types of compatible types (`address[] vs
  address payable[]`, `address[] vs interface[]`, `address[] vs
  contract[]`, `uint160[] vs address[]`, `uint256[] vs bytes32[]`,
  `uint256[N] vs bytes32[N]`, etc.), instead of the naive approach of
  creating a new array and copying all items from the old array, assign
  one array pointer to the other via `assembly { newArr := oldArr }`.
  The same trick can be applied to compatible structs.
* To shorten a dynamic memory array, do `assembly { mstore(arr, newSize)
  }`, since the size is stored in the first slot in memory.
* To shorten a static memory array, create a new static array with the
  required size and simply `assembly { newArr := oldArr }`.

## Low level

* When dealing with revert bytes, never bubble up with
  `revert(string(revertBytes))`; this is wrong as it re-encodes the
  revert data as an `Error(string)` revert type. Instead do
  `assembly { revert(add(revertBytes, 0x20), mload(revertBytes)) }`.

## ERC20

* If a contract needs to spend ERC20 tokens from a user, leverage
  [EIP-2612](https://eips.ethereum.org/EIPS/eip-2612) to avoid requiring
  the user to first `approve` our contract in the ERC20 contract.

## Uniswap v4 Pool Initialization Pattern

When initializing Uniswap v4 pools and adding initial liquidity,
**always use `PoolInitializer_v4` with `Multicall_v4`** to atomically
combine pool initialization and liquidity deposit in a single transaction.
This prevents front-running attacks where an attacker could:

1. Front-run pool initialization to set a manipulated `sqrtPriceX96`
2. Front-run the initial liquidity deposit to extract value from LPs
3. Execute swaps in empty pools to manipulate the price before liquidity is added

**Required Pattern:**

* Use `PositionManager.multicall()` to bundle `initializePool()` and
  `modifyLiquidities()` calls
* Always include slippage protection when adding initial liquidity
* Never split pool initialization and initial deposit across separate
  transactions

**Reference:** OpenZeppelin Uniswap v4 Core Audit - Medium Severity:
["Front-Running Pool's Initialization or Initial Deposit Can Lead to
Draining Initial Liquidity"](https://www.openzeppelin.com/news/uniswap-v4-core-audit#medium-severity)

## Testing

The following testing practices should be followed when writing unit
tests for new code. All functions, lines and branches should be tested to
result in 100% testing coverage. Fuzz parameters and conditions whenever
possible. Extremes should be tested in dedicated edge case and corner
case tests. Invariants should be tested in dedicated invariant tests.

Differential testing should be used to compare assembly implementations
with implementations in Solidity or testing alternative implementations
against existing Solidity or non-Solidity code using ffi.

New features must be merged with associated tests. Bug fixes should have
a corresponding test that fails without the bug fix.

## Further Reading

Ensure to apply all guidelines outlined below on top of the above:

* [Solidity style guide](https://docs.soliditylang.org/en/latest/style-guide.html)
* [OpenZeppelin conventions](https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/GUIDELINES.md#solidity-conventions)
