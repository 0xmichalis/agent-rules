# PR review poll

Starts an agent review session in Orca when someone mentions you in Slack with a
link to a pull request in your GitHub organization. Nobody has to create a Slack
app: the poll uses your own claude.ai Slack connector.

## How it works

A systemd user timer runs `pr_review_poll.py run` every minute; systemd never
starts a run while the previous one is still going. Each run has three steps.

1. Housekeeping. Every three minutes it checks the pull requests of the sessions
   it started. New commits, new comments from people or a new Slack request are
   sent to the session's agent as a message; a busy agent takes it after its
   current turn. When all of a session's pull requests have merged or closed,
   its tab is closed. At most three agents review at once; queued requests start
   when one finishes.
2. Poll. A headless Claude Haiku session in restricted mode searches Slack for
   messages that mention you, starting 30 minutes before the last successful
   poll, because Slack search can return a message minutes after it was posted.
   Messages already handled in that window are listed in the prompt. A run in
   which the search did not happen counts as failed and leaves that starting
   point alone. For each message with a pull request link it runs
   `pr_review_poll.py submit`. It can run no other command beyond read-only
   shell built-ins, and it ignores your settings files.
3. Submit. The dispatcher validates the permalink, author and pull request URLs
   and ignores messages it has handled. It skips pull requests that are merged
   or closed, yours, opened from a fork or approved by you at the current head.
   It starts one agent per message with `orca agent launch`, as a tab named
   `review-<repo>-<number>` in the Orca workspace that contains `REVIEW_CWD`.
   The agent's prompt contains only the validated URLs. If the agent cannot
   start, for example because Orca is closed, the request is queued and retried.

`REVIEW_AGENT`, `REVIEW_MODEL` and `REVIEW_EFFORT` choose the agent, which
default to `claude`, `claude-opus-5-5` and `xhigh`. Orca starts the agent with
the arguments from your Orca agent settings.

Review sessions never approve. When a pull request is ready, the agent sends a
push notification if it can and waits; open its tab in Orca and ask it to
approve.

## Requirements

- Linux with a systemd user manager.
- Orca running, with `REVIEW_CWD` inside one of its workspaces.
- Claude Code signed in to a claude.ai account with the Slack connector
  connected. The poll always uses Claude, whatever the review agent is.
- `gh` signed in with access to the organization.

## Set up

Install the snapshot from this checkout:

```bash
python3 scripts/install.py
```

Create `~/.config/pr-review-poll/env` with your values:

```sh
SLACK_USER_ID=U0123ABCD
SLACK_DOMAIN=example.slack.com
GITHUB_ORG=ExampleOrg
GITHUB_LOGIN=your-github-login
REVIEW_CWD=/absolute/path/to/your/workspace
ORCA_CLI_COMMAND=/absolute/path/to/orca-cli
REVIEW_AGENT=claude
REVIEW_MODEL=claude-opus-5-5
REVIEW_EFFORT=xhigh
```

Set `ORCA_CLI_COMMAND` to the value of `$ORCA_CLI_COMMAND` in an Orca terminal.
Outside Orca's terminals, `orca` on Linux usually starts the GNOME screen
reader, and an older `orca-ide` may not have the agent commands. The last three
lines are optional.

Replay the last day without starting sessions. It uses separate state and
prints what it would do:

```bash
systemd-run --user --wait --pipe --collect \
  -p EnvironmentFile="$HOME/.config/pr-review-poll/env" \
  -E PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin" \
  -E PR_REVIEW_POLL_DRY_RUN=1 \
  -E PR_REVIEW_POLL_STATE_DIR="$HOME/.local/state/pr-review-poll-dry-run" \
  "$HOME/.agents/agent-rules/automations/pr-review-poll/pr_review_poll.py" \
  run --since "$(date -d '1 day ago' +%s)"
```

Link the service, then enable the timer:

```bash
systemctl --user link \
  ~/.agents/agent-rules/automations/pr-review-poll/systemd/pr-review-poll.service
```

```bash
systemctl --user enable --now \
  ~/.agents/agent-rules/automations/pr-review-poll/systemd/pr-review-poll.timer
```

Follow the runs:

```bash
journalctl --user -u pr-review-poll.service -f
```

Each start, wake, skip and retirement is also appended to
`~/.local/state/pr-review-poll/events.log`. Stop polling with:

```bash
systemctl --user disable --now pr-review-poll.timer
```

## Limits

- It runs only while you are logged in. After a gap, the next poll searches
  from the last successful poll, so requests are delayed, not lost.
- If no poll succeeds for 15 minutes, for example because the Slack connector
  needs reauthorizing in claude.ai, it sends a desktop notification, repeated
  at most hourly.
- Slack's search index can lag a message by up to a minute or so.
- Sessions are tracked by their Orca pane. If a tab is closed or Orca loses it,
  the session is forgotten and the next request for its pull requests starts a
  new one. Requests that cannot start for 15 minutes send a desktop
  notification.
- A message whose pull request link the poll cannot pass on is rejected and
  logged; it is retried until it falls out of the 30-minute overlap.
