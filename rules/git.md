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
* Review the current PR head, not an assumed matching local checkout. Look
  outside the diff: other readers of changed data and APIs, stored data and
  rollback, library behavior at the pinned version, deploy order, alerts, and
  whether the tests can fail. Back substantive findings with code evidence, a
  focused reproduction or a read of live state. Check relevant CI before
  approving; obey platform self-review restrictions.
* Leave approval summaries empty by default; put non-blocking notes inline and
  leave resolving them to the author. On your own PRs, reply in each addressed
  thread and resolve completed work; avoid duplicate replies.
* Check available review comments and CI before handoff and address actionable
  feedback. Automatic reviewers can post minutes after a push; wait for their
  review of the current head before merging.
* In public repositories, don't mention private repos in commits, code
  comments, PR text or review replies.
* After an owned PR update, fast-forward a matching user checkout only when its
  state permits it; stop on divergence. Never reset or stash the user's work to
  force synchronization.
* Once the task and feedback are handled, remove clean worktrees you created;
  preserve branches needed by open PRs. Delete branches after an authorized PR
  closure only when no checkout holds them and no unique work would be lost.
* Use full PR/issue URLs and published commit permalinks for precise code
  evidence. Keep human co-authorship; omit AI/model/session attribution unless
  the target project requires disclosure.
