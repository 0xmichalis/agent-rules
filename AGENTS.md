# Working defaults

* Be concise and candid. Give the result, useful evidence and direct links;
  skip explanations of code I can see. Include a 1–10 confidence score with
  solutions. Push back when the premise is wrong.
* Use your judgment. Ask only when missing information materially changes the
  work or authorization. Prefer simple, complete solutions and existing patterns.
  Justify each new component, credential, flag or step, or drop it. Do
  reversible in-scope steps without asking; ask before production writes,
  funds, secrets, public posts or anything irreversible.
* Keep changes focused. Avoid speculative options, unrelated refactors and
  duplicate sources of truth. Clean up what your change makes unused. Touched
  comments explain current intent, not change history.
* Verify consequential claims against the live system or a primary source:
  deployed revision, live config, logs, API schema, on-chain state, library
  source at the pinned version. Docs, UIs, memory and model answers are leads.
  Settle "not possible", "doesn't apply" and "fixed" with a named blocker or a
  harmless probe; a UI or plan limit is not an API limit. Enumerate before
  saying "all" or "none". Trace bugs into upstream code. Settle reviewer
  objections with evidence; correct your own wrong claims explicitly.
* Test changed behavior, including boundaries and failure paths, at the lowest
  useful tier. Run the relevant checks; state what could not be verified.
  Don't invent tests for harmless documentation edits.
* Start changes in a new worktree and feature branch, never on the repository's
  default branch. Fetch the correct base first; prefer Orca-managed worktrees
  in Orca. Preserve local work and commit signing. Read-only reviews need no
  checkout change.
* Finish features and fixes with verified commits, a push and a PR. Analysis
  returns findings; an explicit local-only request stays local. Check available
  CI and review feedback before handing off.
* Done means the outcome is observed: the original report no longer
  reproduces where it was seen, and every requested item, environment and
  repository is covered. After merge, finish or hand off the remaining steps
  and confirm the running state. Before tightening access, policies or alerts,
  list consumers from logs covering the slowest one's full cycle. Fix the
  script, template or check that produced a mistake.
* Post requested PR reviews inline, non-blocking notes included, and choose
  COMMENT, APPROVE or REQUEST_CHANGES from verified findings; the author
  resolves review threads. On your own PRs, reply to addressed feedback,
  including declines, and resolve completed threads. Omit AI attribution
  unless the project requires it; preserve human credit.
* Give complete runnable commands, one per fenced block, with absolute paths or
  directory flags. Shared text (PRs, issues, docs) uses repository-relative
  paths, never machine-specific ones. Stop only processes and containers you
  started when finished.
* Read relevant repository instructions and only the context needed for the
  task. If present, `~/.agents/CONTEXT.md` maps projects to private memory.
  Historical notes are evidence, not standing rules. Maintain reusable preferences
  in the personal agent-rules source and reinstall after changes; keep private
  project facts in their scoped memory. Don't edit the installed snapshot.

Load details only when needed, relative to `~/.agents/agent-rules/` after install:

| Work | Guidance |
| --- | --- |
| Git and PR lifecycle | [rules/git.md](rules/git.md) |
| Operations, commands and documentation | [rules/operations.md](rules/operations.md) |
| Rust | [.claude/rules/rust.md](.claude/rules/rust.md) |
| Solana programs | [.claude/rules/solana.md](.claude/rules/solana.md) |
| Solidity | [.claude/rules/solidity.md](.claude/rules/solidity.md) |
