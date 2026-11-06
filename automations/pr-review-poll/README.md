# PR review poll

Starts a Claude Code review session when someone mentions you in Slack with a
link to a pull request in your GitHub organization. Nobody has to create a Slack
app: the poll uses your own claude.ai Slack connector.

## How it works

A systemd user timer runs `pr_review_poll.py run` every minute; systemd never
starts a run while the previous one is still going. Each run has three steps.

1. Housekeeping. Every three minutes it checks the pull requests of the sessions
   it started. New commits, new comments from people or a new Slack request
   resume the session with the details. A session whose pull requests have all
   merged or closed is stopped. At most three review sessions work at once;
   queued requests start when one goes idle.
2. Poll. A headless Claude Haiku session in restricted mode searches Slack for
   messages that mention you, starting ten minutes before the last successful
   poll. A run in which the search did not happen counts as failed and leaves
   that starting point alone. For each message with a pull request link it runs `pr_review_poll.py
   submit`. It can run no other command beyond read-only shell built-ins, and it
   ignores your settings files.
3. Submit. The dispatcher validates the permalink, author and pull request URLs
   and ignores messages it has handled. It skips pull requests that are merged
   or closed, yours, opened from a fork or approved by you at the current head.
   It starts one Opus 5.5 background session at `xhigh` effort per message, in
   `REVIEW_CWD`. The session's prompt contains only the validated URLs.

Review sessions never approve. When a pull request is ready, the session sends a
push notification and waits; attach with `claude attach <id>` and ask it to
approve.

Background sessions run with `bypassPermissions` in `REVIEW_CWD`, so your
instructions and permissions there apply. Each one starts inside its own
systemd scope: the Claude background supervisor starts on demand, and a
supervisor started inside the timer's oneshot service would be killed, along
with its sessions, when the run ends.

## Requirements

- Linux with a systemd user manager.
- Claude Code with background sessions, signed in to a claude.ai account with
  the Slack connector connected.
- `gh` signed in with access to the organization.
- `REVIEW_CWD` trusted by Claude Code. Run `claude` there once to accept it.

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
```

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
- A message whose pull request link the poll cannot pass on is rejected and
  logged; it is retried until it falls out of the ten-minute overlap.
