# Agent guidelines

## Communication

I am an experienced software engineer. Be succinct: skip the deep
explanation unless I ask for it, and don't narrate code I can already read
in my IDE.

Be radically candid. Don't try to please me, and push back when I'm wrong.

When you propose a solution, rate your confidence in it 1-10.

## Working agreement

* Follow the 4 rules of simple design: passes tests, reveals intent,
  minimizes duplication, minimal set of elements.
* Every changed line should trace to something I asked for. Don't improve
  adjacent code, don't rename or refactor what I didn't point you at, and
  don't add configurability or error handling for cases that can't happen.
* Clean up the orphans your own change creates. Leave pre-existing dead code
  alone — mention it instead of deleting it.
* Keep existing comments; rewrite one only when your change made it wrong.
  Don't leave a tombstone comment where you deleted code.
* Surface confusion before writing code, not after. If two readings of the
  request lead to different work, ask.

## Verification

Turn the task into something you can check, then loop until it passes:

* "Add validation" → write tests for the invalid inputs, then make them pass
* "Fix the bug" → write a test that reproduces it, then make it pass
* "Refactor X" → tests green before and after

Prefer exact equality assertions over approximate comparisons. Don't put
comments inside bash commands you execute.

## Topic rules

These hold gotchas and opinions, not language basics. Load the one that
matches the work; ignore the rest.

| Rules | Load when |
| --- | --- |
| [AGENTS-rust.md](./AGENTS-rust.md) | Writing or reviewing Rust |
| [AGENTS-solana.md](./AGENTS-solana.md) | Solana programs, Anchor, CPI, PDAs |
| [AGENTS-solidity.md](./AGENTS-solidity.md) | Solidity contracts, EVM, gas |
| [AGENTS-sql.md](./AGENTS-sql.md) | Designing or auditing database indexes |
| [AGENTS-github.md](./AGENTS-github.md) | Driving GitHub through `gh` |

Claude Code loads these automatically through the skills in
[.claude/skills](./.claude/skills) — no `@` mention needed.
