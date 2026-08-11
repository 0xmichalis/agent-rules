---
name: github-cli
description: Driving GitHub through the gh CLI — reading issues with comments, fetching PR reviews and inline review comments, replying inline via in_reply_to, and the REST workaround for gh pr edit's missing OAuth scope. Load when reading or responding to GitHub issues and pull requests.
---

# GitHub CLI

Read `AGENTS-github.md` at the root of the agent-rules repo
(`../../../AGENTS-github.md` relative to this skill) and apply it.

Two things that will otherwise cost you a round trip:
`/pulls/comments/<id>/replies` returns 404, and `gh pr edit` fails without
the `read:project` scope.
