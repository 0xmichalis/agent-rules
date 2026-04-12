# Agent guidelines

## Golden Communication Rule #1

I am an experienced software engineer. This means there is no need for deep
explanations unless specifically asked. Be succinct and to the point in all
your code, documentation and explanations unless explicitly asked for more
details. I see all the code you generate in my IDE, avoid superfluously
summarizing what you did in text.

## Behavior guidelines

* BE RADICALLY CANDID in all conversation, don't try to please me and don't be
  afraid to push back.
* When providing a solution, give me a score on a scale of 1-10 about how
  confident you are in the solution.

## Design & code defaults

* Always follow the 4 rules of simple design (code that passes tests, reveals
  intent, minimizes duplication, has a minimal set of elements).
* Never remove comments unless the code you update renders the comment
  invalid.
* Never refactor or rename code unless you are explicitly being told so
* When removing code, do not add a comment to note the deletion of the code,
  simply delete the code

## Tests & commands

* Always try to use exact equality assertions instead of approximate comparisons
  in tests
* Avoid using bash comments when executing commands

## Planning & execution

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

* State your assumptions explicitly. If uncertain, ask.
* If multiple interpretations exist, present them - don't pick silently.
* If a simpler approach exists, say so. Push back when warranted.
* If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

* No features beyond what was asked.
* No abstractions for single-use code.
* No "flexibility" or "configurability" that wasn't requested.
* No error handling for impossible scenarios.
* If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

* Don't "improve" adjacent code, comments, or formatting.
* Don't refactor things that aren't broken.
* Match existing style, even if you'd do it differently.
* If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

* Remove imports/variables/functions that YOUR changes made unused.
* Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

* "Add validation" → "Write tests for invalid inputs, then make them pass"
* "Fix the bug" → "Write a test that reproduces it, then make it pass"
* "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```text
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it
work") require constant clarification.

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
* `gh pr edit` requires the `read:project` OAuth scope which may not be available.
  Use the REST API instead:
  `gh api repos/:owner/:repo/pulls/<pr_number> -X PATCH -f body="..." -f title="..."`
* For quick inspection, you can pipe JSON through `jq`, for example:
  * `gh api repos/:owner/:repo/pulls/105/reviews | jq '.[].id, .[].user.login'`
  * `gh api repos/:owner/:repo/pulls/105/reviews/<review_id>/comments | jq '.[].body'`
  * `gh api repos/:owner/:repo/pulls/105/comments | jq '.[].id, .[].body'`

## MCP Tools (Notion, Linear, Slack)

MCP tools from cloud integrations are **deferred** — they must be loaded via
`ToolSearch` before they can be called. Without loading first, calls fail with
"No such tool available".

* Tool naming pattern: `mcp__claude_ai_<Server>__<tool-name>`
* Load tools with `ToolSearch` using a `+` prefix query:
  * `"+notion"` — loads Notion tools (`notion-search`, `notion-fetch`,
    `notion-create-pages`, `notion-update-page`, `notion-move-pages`, etc.)
  * `"+linear"` — loads Linear tools (`list_issues`, `save_issue`,
    `list_projects`, etc.)
  * `"+slack"` — loads Slack tools (`slack_send_message`, `slack_read_channel`,
    `slack_search_public`, etc.)
* Once loaded via `ToolSearch`, the tools are available for the rest of the
  session — no need to load again.
* **Do NOT** guess tool names and call them directly. Always load via
  `ToolSearch` first.
