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
models](https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models).

## Structure

| File | Contents |
| --- | --- |
| [AGENTS.md](./AGENTS.md) | Always-loaded: communication, working agreement, verification, index |
| [AGENTS-rust.md](./AGENTS-rust.md) | Rust conventions |
| [AGENTS-solana.md](./AGENTS-solana.md) | Solana program security |
| [AGENTS-solidity.md](./AGENTS-solidity.md) | Solidity contracts |
| [AGENTS-sql.md](./AGENTS-sql.md) | Database index design |
| [AGENTS-github.md](./AGENTS-github.md) | `gh` CLI recipes |
| [.claude/skills/](./.claude/skills) | Trigger descriptions that load the topic files on demand |

## Usage

Symlink `AGENTS.md` into a project root so it keeps resolving against this
checkout:

```bash
ln -sfn ~/path/to/agent-rules/AGENTS.md /path/to/project/AGENTS.md
```

If you copy it instead, copy the whole set — `AGENTS.md` links to the topic
files by relative path, and a lone copy leaves those links dangling.

For Claude Code, install the skills once so topic rules load automatically
by trigger instead of by `@` mention:

```bash
mkdir -p ~/.claude/skills
for s in .claude/skills/*/; do
  ln -sfn "$PWD/${s%/}" ~/.claude/skills/
done
```

Each skill reads its topic file from this checkout, so keep the repo where
it is after linking.

## License

Dual-licensed.

### GPL v3.0

[AGENTS-rust.md](./AGENTS-rust.md) is derived from [Canonical's Rust Best
Practices](https://canonical.github.io/rust-best-practices/) and is
licensed under the GNU General Public License v3.0.

### MIT

Everything else — `AGENTS.md`, `AGENTS-github.md`, `AGENTS-solana.md`,
`AGENTS-solidity.md`, `AGENTS-sql.md`, `.claude/skills/`, `README.md` — is
licensed under the MIT License.

## Contributing

Contributions are welcome. Please comply with the licensing terms of the
respective files, and keep new rules to things that aren't obvious to a
current-generation model.
