# Git and pull requests

* Start changes in a new worktree and feature branch, never on the repository's
  default branch. Fetch before starting and use the intended PR base.
* Never move or delete a branch held by another worktree. Stage relevant files
  explicitly, retain signing and avoid direct pushes to protected branches.
* Keep meaningful commits self-contained. Fold corrections into their owning
  commits when appropriate. Rewrite published history only when authorized,
  on an owned branch, with an explicit lease; preserve other people's commits.
* A fix to a PR you maintain includes pushing the update. A request for a local
  commit without publication stays local. Existing user instructions control
  whether an unrelated branch should be published.
* Review the current PR head, not an assumed matching local checkout. Back
  substantive findings with code evidence or a focused reproduction. Check
  relevant CI before approving; obey platform self-review restrictions.
* Leave approval summaries empty by default; put non-blocking notes inline.
  Reply in each addressed thread and resolve completed work; avoid duplicate
  replies.
* Check available review comments and CI before handoff and address actionable
  feedback.
* After an owned PR update, fast-forward a matching user checkout only when its
  state permits it; stop on divergence. Never reset or stash the user's work to
  force synchronization.
* Once the task and feedback are handled, remove clean worktrees you created;
  preserve branches needed by open PRs. Delete branches after an authorized PR
  closure only when no checkout holds them and no unique work would be lost.
* Use full PR/issue URLs and published commit permalinks for precise code
  evidence. Keep human co-authorship; omit AI/model/session attribution unless
  the target project requires disclosure.
