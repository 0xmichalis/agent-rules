---
name: github-cli
description: Driving GitHub through the gh CLI — reading issues with comments, fetching PR reviews and inline review comments, replying inline via in_reply_to, and the REST workaround for gh pr edit's missing OAuth scope. Load when reading or responding to GitHub issues and pull requests.
---

# GitHub Guidelines

Working with GitHub through the `gh` CLI. These are the endpoints and
workarounds that aren't discoverable from `gh --help`.

`gh` expands `{owner}` and `{repo}` from the current directory. Everything
in angle brackets is a placeholder you substitute before running.

## Reading

* When a GitHub link isn't reachable by web search, fetch it with `gh`.
* `gh issue view <id> --comments` — always read the comments, not just the
  issue body.
* Reviews on a PR:
  `gh api --paginate repos/{owner}/{repo}/pulls/<pr>/reviews`
* Comments within one review:
  `gh api --paginate repos/{owner}/{repo}/pulls/<pr>/reviews/<review_id>/comments`
* All inline review comments on a PR:
  `gh api --paginate repos/{owner}/{repo}/pulls/<pr>/comments`

List endpoints return 30 items per page; without `--paginate` a busy PR
silently loses comments.

Pipe through `jq` to keep the output small:

```bash
gh api --paginate repos/{owner}/{repo}/pulls/<pr>/reviews | jq '.[].id, .[].user.login'
gh api --paginate repos/{owner}/{repo}/pulls/<pr>/comments | jq '.[].id, .[].body'
```

## Writing

Reply to a review comment inline by POSTing with `in_reply_to` set to the
parent comment ID:

```bash
gh api repos/{owner}/{repo}/pulls/<pr>/comments \
  -X POST -f body="reply text" -F in_reply_to=<comment_id>
```

`/pulls/comments/<id>/replies` does **not** exist and returns 404.

`gh pr edit` needs the `read:project` OAuth scope, which often isn't
granted. Patch the PR directly instead:

```bash
gh api repos/{owner}/{repo}/pulls/<pr> -X PATCH \
  -f body="..." -f title="..."
```
