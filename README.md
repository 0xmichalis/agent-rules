# Agent Rules

Guidelines for AI coding assistants, organized for progressive disclosure:
a small root file that's always in context, and topic files that get loaded
only when the work touches them.

## Philosophy

These files hold opinions and gotchas — not language basics the model
already knows and not anything a linter or compiler enforces. Rules stay
prescriptive where mistakes are expensive (Solidity and Solana security)
and give way to judgement everywhere else.

The structure follows Anthropic's
[The new rules of context engineering for Claude 5 generation
models](https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models)
and Claude Code's
[memory layout](https://code.claude.com/docs/en/memory): always-loaded
instructions, path-scoped rules, and task-triggered skills.

## Structure

| Path | Contents | Loaded |
| --- | --- | --- |
| [AGENTS.md](./AGENTS.md) | Communication, working agreement, verification, index | Always |
| [.claude/rules/rust.md](./.claude/rules/rust.md) | Rust conventions | Touching `*.rs` |
| [.claude/rules/solana.md](./.claude/rules/solana.md) | Solana program security | Touching `programs/**/*.rs` or `Anchor.toml` |
| [.claude/rules/solidity.md](./.claude/rules/solidity.md) | Solidity contracts | Touching `*.sol` |
| [.claude/skills/sql-indexes](./.claude/skills/sql-indexes/SKILL.md) | Database index design | Index or slow-query work |
| [.claude/skills/github-cli](./.claude/skills/github-cli/SKILL.md) | `gh` CLI recipes | Reading or responding on GitHub |

Each rule file carries a `paths` front matter block that Claude Code uses
to decide when to load it. Skills load on their `description`.

## Usage

### Claude Code

Install once; every project on the machine then gets the rules and skills
without any per-project setup:

```bash
mkdir -p ~/.claude/rules ~/.claude/skills
ln -sfn "$PWD/.claude/rules" ~/.claude/rules/agent-rules
for s in .claude/skills/*/; do
  ln -sfn "$PWD/${s%/}" ~/.claude/skills/
done
```

Then import the root file from your user memory so it is always in context:

```bash
echo "@$PWD/AGENTS.md" >> ~/.claude/CLAUDE.md
```

Each link points back into this checkout, so keep the repo where it is
after linking.

### Other agents

Symlink `AGENTS.md` into a project root:

```bash
ln -sfn ~/path/to/agent-rules/AGENTS.md /path/to/project/AGENTS.md
```

If you copy it instead, copy the whole set — `AGENTS.md` links to the topic
files by relative path, and a lone copy leaves those links dangling.

## License

Dual-licensed.

### GPL v3.0

[.claude/rules/rust.md](./.claude/rules/rust.md) is derived from
[Canonical's Rust Best
Practices](https://canonical.github.io/rust-best-practices/) and is
licensed under the GNU General Public License v3.0.

### MIT

Everything else — `AGENTS.md`, `README.md`, the remaining files under
`.claude/rules/` and `.claude/skills/` — is licensed under the MIT License.

## Contributing

Contributions are welcome. Please comply with the licensing terms of the
respective files, and keep new rules to things that aren't obvious to a
current-generation model.
