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
* Never mention the model or tool that wrote the code in commit messages or
  PR descriptions.

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

Rules are tied to file types and load when you touch a matching file:

| Rule | Files |
| --- | --- |
| [rust.md](./.claude/rules/rust.md) | `**/*.rs` |
| [solana.md](./.claude/rules/solana.md) | `**/programs/**/*.rs`, `**/Anchor.toml` |
| [solidity.md](./.claude/rules/solidity.md) | `**/*.sol` |

Skills are tied to a task rather than a file:

| Skill | Load when |
| --- | --- |
| [sql-indexes](./.claude/skills/sql-indexes/SKILL.md) | Designing or auditing database indexes, diagnosing a slow query |
| [github-cli](./.claude/skills/github-cli/SKILL.md) | Driving GitHub through `gh` |

Claude Code loads both automatically once installed as described in the
[README](./README.md) — no `@` mention needed.
