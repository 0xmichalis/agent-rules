# GitHub Guidelines

Working with GitHub through the `gh` CLI. These are the endpoints and
workarounds that aren't discoverable from `gh --help`.

## Reading

* When a GitHub link isn't reachable by web search, fetch it with `gh`.
* `gh issue view <id> --comments` — always read the comments, not just the
  issue body.
* Reviews on a PR: `gh api repos/:owner/:repo/pulls/<pr>/reviews`
* Comments within one review:
  `gh api repos/:owner/:repo/pulls/<pr>/reviews/<review_id>/comments`
* All inline review comments on a PR:
  `gh api repos/:owner/:repo/pulls/<pr>/comments`

Pipe through `jq` to keep the output small:

```bash
gh api repos/:owner/:repo/pulls/105/reviews | jq '.[].id, .[].user.login'
gh api repos/:owner/:repo/pulls/105/comments | jq '.[].id, .[].body'
```

## Writing

Reply to a review comment inline by POSTing with `in_reply_to` set to the
parent comment ID:

```bash
gh api repos/:owner/:repo/pulls/<pr>/comments \
  -X POST -f body="reply text" -F in_reply_to=<comment_id>
```

`/pulls/comments/<id>/replies` does **not** exist and returns 404.

`gh pr edit` needs the `read:project` OAuth scope, which often isn't
granted. Patch the PR directly instead:

```bash
gh api repos/:owner/:repo/pulls/<pr> -X PATCH \
  -f body="..." -f title="..."
```
