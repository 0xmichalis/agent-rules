# Guidelines

## General Guidelines

* Never remove comments unless the code you update renders the comment
  invalid.
* Never refactor or rename code unless you are explicitly being told so.
* When removing code, do not add a comment to note the deletion of the code,
  simply delete the code.
* Always try to use exact equality assertions instead of approximate comparisons
  in tests.
* When providing a solution, give me a score on a scale of 1-10 about how
  confident you are in the solution.

## GitHub Guidelines

* When you cannot access a GitHub link via a web search, try using the `gh` command.
* Read an issue and all its comments with `gh issue view <id> --comments`.
  When you read an issue, always read all the comments.
* List reviews on a PR:
  `gh api repos/:owner/:repo/pulls/<pr_number>/reviews`
* Fetch all review comments for a specific review:
  `gh api repos/:owner/:repo/pulls/<pr_number>/reviews/<review_id>/comments`
* List all review comments (inline comments) on a PR:
  `gh api repos/:owner/:repo/pulls/<pr_number>/comments`
* Reply to a review comment inline: POST to the PR comments endpoint with
  `in_reply_to` set to the parent comment ID:

  ```bash
  gh api repos/:owner/:repo/pulls/<pr_number>/comments \
    -X POST -f body="reply text" -F in_reply_to=<comment_id>
  ```

* **Do NOT** use `/pulls/comments/<id>/replies` — that endpoint does not exist
  and returns 404.
* For quick inspection, you can pipe JSON through `jq`, for example:
  * `gh api repos/:owner/:repo/pulls/105/reviews | jq '.[].id, .[].user.login'`
  * `gh api repos/:owner/:repo/pulls/105/reviews/<review_id>/comments | jq '.[].body'`
  * `gh api repos/:owner/:repo/pulls/105/comments | jq '.[].id, .[].body'`

## Markdown Guidelines

* If available, use `markdownlint` to lint Markdown files.
