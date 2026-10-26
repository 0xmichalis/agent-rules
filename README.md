# Agent Rules

Personal defaults shared by coding agents and models. The root instructions stay
small; load one relevant topic instead of reading a rule catalog on every task.

## Install

From this checkout, using Python 3.10 or later on Linux or macOS:

```bash
python3 scripts/install.py
```

The installer puts a self-contained snapshot in `~/.agents/agent-rules/` and
links Codex and Claude Code to the same `AGENTS.md`. Hermes receives the same
defaults in a managed section of its global `SOUL.md`:

| Runner | Global entry |
| --- | --- |
| Codex | `~/.codex/AGENTS.md` |
| Claude Code | `~/.claude/CLAUDE.md` |
| Hermes | `~/.hermes/SOUL.md` (managed section) |

Existing instructions and previous installations are backed up under
`~/.agents/backups/agent-rules/`. A failed replacement attempts to restore every
previous entry; rollback failures report the retained backup location without
hiding the installation error. Re-running the installer updates every entry to
the same content; removing the source worktree does not break installed rules.

Claude's `~/.claude/rules/agent-rules` also points to the installed language rules,
retaining their file-type filters. Any existing copy or link is backed up first.

Hermes personality text outside the managed section is preserved. Existing
profiles under `~/.hermes/profiles/` receive the defaults too; rerun after adding
a profile. Hermes loads this content globally, independently of project
instructions; see its [context-file documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files).

Start a new agent session after installation. Orca's managed profiles may mirror
these native files; verify the effective entry when using a custom account,
`CODEX_HOME`, `HERMES_HOME`, SSH, WSL, or another host. Install on each execution
host that needs these preferences. Other runners need their global entry pointed
at the same installed source.

Do not symlink this root over a project's own `AGENTS.md`: global personal
preferences and repository instructions serve different scopes.

## Context budget

[AGENTS.md](AGENTS.md) contains the standing defaults. Its topic links are
instructions to read a relevant file, not a reason to preload all of them.
After install, resolve those links under `~/.agents/agent-rules/`.

| Load when | Guidance |
| --- | --- |
| Git history, review, or PR cleanup needs detail | [rules/git.md](rules/git.md) |
| Operating services or writing a runbook | [rules/operations.md](rules/operations.md) |
| Editing Rust | [.claude/rules/rust.md](.claude/rules/rust.md) |
| Working on a Solana program | [.claude/rules/solana.md](.claude/rules/solana.md) |
| Editing Solidity | [.claude/rules/solidity.md](.claude/rules/solidity.md) |
| Designing indexes or diagnosing a slow query | [.claude/skills/sql-indexes/SKILL.md](.claude/skills/sql-indexes/SKILL.md) |
| Needing detailed GitHub CLI recipes | [.claude/skills/github-cli/SKILL.md](.claude/skills/github-cli/SKILL.md) |

The existing skill files are included as references. Automatic skill discovery
is runner-specific; other agents read the linked language guidance on demand.
Don't install a whole directory as unconditional startup text.

## Private context

Keep project memory, organization rules, credentials and session histories out of
this repository. A local `~/.agents/CONTEXT.md` can map repository owners or paths
to private rule and memory indexes. Match the current project, read its short
index, then retrieve only relevant notes. Treat historical notes as evidence to
verify, not instructions that override current preferences.

Save broadly reusable preferences here. Save project facts in the owning private
memory. Archive superseded feedback instead of growing the startup rule list.

## Validation

```bash
python3 -m unittest discover -s tests -v
```

CI also lints Markdown. Installation tests cover shared content, updates, existing
instruction backups, private-context preservation and rollback after failure.

## License

Dual-licensed.

### GPL v3.0

[.claude/rules/rust.md](.claude/rules/rust.md) is derived from
[Canonical's Rust Best Practices](https://canonical.github.io/rust-best-practices/)
and is licensed under the GNU General Public License v3.0.

### MIT

Everything else is licensed under the MIT License.

## Contributing

Keep instructions consequential and scoped. Omit language basics and rules that
are already enforced by tooling. Follow the licensing of the file being changed.
