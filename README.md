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
| Hermes | `$HERMES_HOME/SOUL.md` or `~/.hermes/SOUL.md` (managed section) |

Existing instructions and previous installations are backed up under
`~/.agents/backups/agent-rules/`. A failed replacement attempts to restore every
previous entry; rollback failures report the retained backup location without
hiding the installation error. Re-running the installer updates every entry to
the same content; removing the source worktree does not break installed rules.

The repository holds only runner-neutral content; the installer maps it into
each runner's native locations:

| Source | Claude Code | Codex |
| --- | --- | --- |
| `rules/scoped/` | `~/.claude/rules/agent-rules` | Linked from `AGENTS.md` |
| `skills/<name>/` | `~/.claude/skills/<name>` | `~/.agents/skills/<name>` |

Scoped rules keep their `paths:` file filters. Links for skills removed from
the repository are archived on the next run. Any existing copy or link is
backed up first.

The installer refuses to change anything when a runner would truncate or reject
the result: a Hermes `SOUL.md` over 20,000 characters, or a skill name or
description over Codex's 64- or 1,024-character limits. Codex's 32 KiB
`project_doc_max_bytes` budget applies to repository `AGENTS.md` files, not
`~/.codex/AGENTS.md`.

Hermes personality text outside the managed section is preserved. The installer
honors `HERMES_HOME`; recognized profiles under that home's `profiles/` receive
the defaults too. Bare directories, deleted profiles and directory symlinks are
skipped. Rerun after adding a profile. Backups for a home outside your user home
are stored under `hermes-home/` in the installation backup directory.

`SOUL.md` applies to every Hermes session using that home, including TUI and
gateway sessions; it is not specific to Orca. A remote gateway uses its own
server-side home and needs installation there. See Hermes's
[context-file documentation](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files).

Upgrades archive the old OpenCode instruction link only if it points to this
installer's shared defaults. Custom OpenCode files and links are preserved.

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
| Performance review | [rules/performance-scout.md](rules/performance-scout.md) |
| Editing Rust | [rules/scoped/rust.md](rules/scoped/rust.md) |
| Working on a Solana program | [rules/scoped/solana.md](rules/scoped/solana.md) |
| Editing Solidity | [rules/scoped/solidity.md](rules/scoped/solidity.md) |
| Designing indexes or diagnosing a slow query | [skills/sql-indexes/SKILL.md](skills/sql-indexes/SKILL.md) |
| Needing detailed GitHub CLI recipes | [skills/github-cli/SKILL.md](skills/github-cli/SKILL.md) |

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

CI also lints Markdown. Installation tests cover runner limits on this
repository's content, shared content, updates, existing instruction backups,
private-context preservation and rollback after failure.

## License

Dual-licensed.

### GPL v3.0

[rules/scoped/rust.md](rules/scoped/rust.md) is derived from
[Canonical's Rust Best Practices](https://canonical.github.io/rust-best-practices/)
and is licensed under the GNU General Public License v3.0.

### MIT

Everything else is licensed under the MIT License.

## Contributing

Keep instructions consequential and scoped. Omit language basics and rules that
are already enforced by tooling. Follow the licensing of the file being changed.
