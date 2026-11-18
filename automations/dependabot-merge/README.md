# Dependabot merge

Approves and merges open Dependabot pull requests whose checks pass and whose
updates are all patch or minor releases. One systemd timer instance runs per
GitHub owner, organization or user, every 30 minutes. It acts as the account
`gh` is signed in to and uses no model.

## Merge rules

A pull request merges only when all of these hold:

- Dependabot opened it, it is not a draft, and you have write access.
- It has a single commit, which Dependabot wrote and GitHub signed, and
  nobody but Dependabot has force-pushed, deleted or restored its branch. A
  commit from anyone else, including an **Update branch** merge, blocks it
  until you comment `@dependabot recreate`.
- Every update in Dependabot's commit metadata is a patch or minor upgrade.
  The first non-zero version component counts as major, so `0.8` to `0.9` and
  `0.0.3` to `0.0.4` are major. A group with one major update is skipped, and
  so are versions that are not plain dotted numbers, such as commit SHAs or
  prereleases. The pull request text is never read.
- Nobody's latest review requests changes.
- Every check on the head commit passed, and at least one of them succeeded
  in a GitHub Actions workflow kept in the repository itself. Checks that an
  organization adds everywhere, such as a ruleset's required workflow from
  another repository, apps and commit statuses, must pass too but are not
  enough on their own, so a repository without its own CI never merges.
- The repository is not on the owner's skip list.
- GitHub reports no merge conflict, and the branch is not behind a base that
  must be up to date.

Right before writing, the job reads the pull request again and applies the
same rules. If the repository still requires a review, it approves the exact
head commit with a comment that names the automation. It skips a pull request
that it has already approved at that commit and that still needs another
review. It then merges that commit by squash, merge commit or rebase, in that
order of preference among the methods the repository allows.

Each run merges the oldest passing update in a repository and leaves the rest
for later runs. Dependabot rebases any that the merge put in conflict, and their
checks run again.

## Requirements

- Linux with a systemd user manager.
- Python 3.10 or later as `python3`, which the installer needs.
- `gh` signed in as the account that approves and merges. In an organization
  whose rules require a code owner's review, that account's approval must
  satisfy them.

## Set up

Install the snapshot from this checkout:

```bash
python3 scripts/install.py
```

Check what the job would do now, without approving or merging. Replace
`ExampleOrg` with your organization or user name:

```bash
~/.agents/agent-rules/automations/dependabot-merge/dependabot_merge.py \
  --owner ExampleOrg --dry-run
```

Each line is JSON: `would_merge` for a pull request the job would merge, and
`skipped` with the reason for the rest.

A merge into a repository whose default branch deploys automatically is a
deploy. Put such repositories on the owner's skip list, which the service reads
from `~/.config/dependabot-merge/<owner>.env`. For example,
`~/.config/dependabot-merge/ExampleOrg.env` could hold:

```text
DEPENDABOT_MERGE_ARGS=--skip-repo web-app --skip-repo api
```

Pass the same `--skip-repo` options to a dry run to check the list.

Link the service and timer templates:

```bash
systemctl --user link \
  ~/.agents/agent-rules/automations/dependabot-merge/systemd/dependabot-merge@.service
```

```bash
systemctl --user link \
  ~/.agents/agent-rules/automations/dependabot-merge/systemd/dependabot-merge@.timer
```

Enable one timer per owner:

```bash
systemctl --user enable --now dependabot-merge@ExampleOrg.timer
```

Follow the runs:

```bash
journalctl --user -u dependabot-merge@ExampleOrg.service -f
```

Stop merging for an owner with:

```bash
systemctl --user disable --now dependabot-merge@ExampleOrg.timer
```

Stop a run that is in progress with the following. Merges that GitHub has
already accepted stay merged.

```bash
systemctl --user stop dependabot-merge@ExampleOrg.service
```

## Limits

- It runs while your systemd user manager runs, which without lingering means
  while you are logged in. A run missed while the machine was off starts when
  the timer is next active.
- A run with a failed approval or merge exits with an error, which
  `systemctl --user list-units --failed` shows. The next run retries.
- The skip list is the only guard against deploys. A repository that starts
  deploying on merge is merged into until you add it.
- In a repository that requires up-to-date branches, a pull request behind its
  base waits until you comment `@dependabot rebase`; Dependabot rebases on its
  own only when the pull request conflicts.
