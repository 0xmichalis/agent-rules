#!/usr/bin/env python3
"""Approve and merge passing patch and minor Dependabot pull requests for one GitHub owner.

A systemd user timer runs this every 30 minutes per owner, as the account `gh` is signed
in to. It lists the open Dependabot pull requests in the owner's unarchived repositories
and merges each one that `blockers` allows, oldest first and at most one per repository
per run, so other updates that now conflict are rebased by Dependabot and checked again
before they merge. When the repository still requires a review, it approves the exact head
commit first. Version changes come from Dependabot's commit message, never the pull
request text. Only a pull request with a single GitHub-signed Dependabot commit, on a branch
nobody else rewrote, is trusted, and a check from the repository's own workflows must pass.
Repositories named with --skip-repo, such as ones that deploy on every merge, are left alone.
"""

import argparse
import json
import re
import subprocess
import sys


DEPENDABOT_LOGIN = "dependabot"
DEPENDABOT_EMAIL = "49699333+dependabot[bot]@users.noreply.github.com"
GITHUB_EMAIL = "noreply@github.com"
WRITE_PERMISSIONS = ("WRITE", "MAINTAIN", "ADMIN")
# In order of preference, among the methods the repository allows.
MERGE_METHODS = (("squashMergeAllowed", "squash"), ("mergeCommitAllowed", "merge"), ("rebaseMergeAllowed", "rebase"))
# Pages of 25 or more pull requests with their commits have failed with HTTP 502.
PAGE_SIZE = 10
GH_TIMEOUT_SECONDS = 120
APPROVAL_BODY = (
    "Approved by the dependabot-merge automation: every update is a patch or minor release,"
    " the only commit is Dependabot's and all checks passed."
)

# The last branch event shows whether anyone but Dependabot replaced the commit, which
# needs a force push or a deleted and restored branch.
PULL_FIELDS = """
fragment pull on PullRequest {
  number url isDraft createdAt headRefOid mergeable mergeStateStatus reviewDecision
  author { login }
  repository { nameWithOwner viewerPermission squashMergeAllowed mergeCommitAllowed rebaseMergeAllowed }
  latestOpinionatedReviews(first: 20) { nodes { state author { login } commit { oid } } }
  timelineItems(itemTypes: [HEAD_REF_FORCE_PUSHED_EVENT, HEAD_REF_DELETED_EVENT, HEAD_REF_RESTORED_EVENT], last: 1) {
    nodes { __typename ... on HeadRefForcePushedEvent { actor { login } afterCommit { oid } } }
  }
  commits(last: 1) { totalCount nodes { commit {
    oid message
    author { email }
    committer { email }
    signature { isValid wasSignedByGitHub }
    statusCheckRollup { state contexts(first: 50) { nodes {
      ... on CheckRun { conclusion checkSuite { workflowRun { file { repositoryName } } } }
    } } }
  } } }
}
"""
SEARCH_QUERY = PULL_FIELDS + """
query($q: String!, $endCursor: String) {
  viewer { login }
  search(query: $q, type: ISSUE, first: %d, after: $endCursor) {
    pageInfo { hasNextPage endCursor }
    nodes { ...pull }
  }
}
""" % PAGE_SIZE
PULL_QUERY = PULL_FIELDS + """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) { pullRequest(number: $number) { ...pull } }
}
"""

FRONT_MATTER = re.compile(r"^---\nupdated-dependencies:\n(.*?)^\.\.\.$", re.M | re.S)
# Dependabot writes a version change as a subject such as "build(deps): bump x from 1.0 to 1.1
# in /dir", a body line "Bumps [x](url) from 1.0 to 1.1." or a group body line "Updates `x`
# from 1.0 to 1.1".
CHANGE = re.compile(
    r"^(?:Bumps \[(?P<linked>[^\]]+)\]\([^)\s]*\)|Bumps (?P<plain>\S+)|Updates `(?P<quoted>[^`]+)`"
    r"|(?:[a-z]+(?:\([a-z-]+\))?: )?[Bb]ump (?P<subject>\S+))"
    r" from (?P<old>\S+) to (?P<new>\S+?)\.?(?: in \S+)?$",
    re.M,
)
VERSION = re.compile(r"v?(\d+(?:\.\d+)*)")


class GitHubError(RuntimeError):
    """A gh call failed; the next run tries again."""


def breaking_change(old, new):
    """Return why a version change is not a patch or minor upgrade, or None."""
    old_match, new_match = VERSION.fullmatch(old), VERSION.fullmatch(new)
    if not old_match or not new_match:
        return f"unrecognised versions {old} -> {new}"
    before = [int(part) for part in old_match.group(1).split(".")]
    after = [int(part) for part in new_match.group(1).split(".")]
    width = max(len(before), len(after))
    before += [0] * (width - len(before))
    after += [0] * (width - len(after))
    if after <= before:
        return f"not an upgrade {old} -> {new}"
    changed = next(index for index in range(width) if before[index] != after[index])
    # Semver treats the first non-zero component as the major one, so 0.8 -> 0.9 breaks.
    major = next((index for index, part in enumerate(before) if part), width - 1)
    if changed <= major:
        return f"major update {old} -> {new}"
    return None


def update_blocker(message):
    """Check every update that Dependabot's commit message records."""
    front_matter = FRONT_MATTER.search(message)
    if not front_matter:
        return "commit message has no Dependabot metadata"
    dependencies = []
    for item in re.split(r"^- ", front_matter.group(1), flags=re.M)[1:]:
        fields = dict(re.findall(r"^\s*([a-z-]+): *(.*?)\s*$", item, flags=re.M))
        dependencies.append((fields.get("dependency-name", "").strip("\"'"), fields.get("update-type", "")))
    if not dependencies:
        return "commit message lists no updated dependencies"
    changes = {}
    for change in CHANGE.finditer(message[: front_matter.start()]):
        name = next(change.group(group) for group in ("linked", "plain", "quoted", "subject") if change.group(group))
        changes.setdefault(name, []).append((change.group("old"), change.group("new")))
    for name, update_type in dependencies:
        if update_type == "version-update:semver-major":
            return f"{name}: major update"
        if name not in changes:
            return f"{name}: version change not found in the commit message"
        for old, new in changes[name]:
            reason = breaking_change(old, new)
            if reason:
                return f"{name}: {reason}"
    return None


def branch_blocker(pr):
    """Trust the branch only if Dependabot alone wrote its single commit."""
    commits = pr["commits"]
    if commits["totalCount"] != 1:
        return f"{commits['totalCount']} commits; only a single Dependabot commit is trusted"
    commit = commits["nodes"][0]["commit"]
    signature = commit.get("signature") or {}
    if (
        commit["oid"] != pr["headRefOid"]
        or (commit.get("author") or {}).get("email") != DEPENDABOT_EMAIL
        or (commit.get("committer") or {}).get("email") != GITHUB_EMAIL
        or not (signature.get("isValid") and signature.get("wasSignedByGitHub"))
    ):
        return f"commit {commit['oid'][:7]} is not a GitHub-signed Dependabot commit"
    events = pr["timelineItems"]["nodes"]
    if events:
        event = events[-1]
        if (
            event.get("__typename") != "HeadRefForcePushedEvent"
            or (event.get("actor") or {}).get("login") != DEPENDABOT_LOGIN
            or (event.get("afterCommit") or {}).get("oid") != pr["headRefOid"]
        ):
            return "branch was last rewritten by someone other than Dependabot"
    return None


def approved_by(pr, login):
    return any(
        (review.get("author") or {}).get("login", "").lower() == login.lower()
        and review.get("state") == "APPROVED"
        and (review.get("commit") or {}).get("oid") == pr["headRefOid"]
        for review in pr["latestOpinionatedReviews"]["nodes"]
    )


def own_check_passed(repository, checks):
    """Whether a check run from a workflow file kept in this repository passed.

    Commit statuses, app checks and workflows kept in another repository, such as the ones an
    organization ruleset requires everywhere, do not show that the repository's own tests ran.
    """
    for check in checks:
        workflow_run = (check.get("checkSuite") or {}).get("workflowRun") or {}
        source = (workflow_run.get("file") or {}).get("repositoryName") or ""
        if check.get("conclusion") == "SUCCESS" and source.lower() == repository.lower():
            return True
    return False


def blockers(pr, viewer):
    """Return the first reason not to merge this pull request, or None."""
    repository = pr["repository"]
    if (pr.get("author") or {}).get("login") != DEPENDABOT_LOGIN:
        return "not opened by Dependabot"
    if pr["isDraft"]:
        return "draft"
    if repository["viewerPermission"] not in WRITE_PERMISSIONS:
        return f"{(repository['viewerPermission'] or 'no').lower()} access to the repository"
    reason = branch_blocker(pr)
    if reason:
        return reason
    head = pr["commits"]["nodes"][0]["commit"]
    reason = update_blocker(head["message"])
    if reason:
        return reason
    # Without a review requirement GitHub may leave reviewDecision empty, so check each review too.
    if pr["reviewDecision"] == "CHANGES_REQUESTED" or any(
        review.get("state") == "CHANGES_REQUESTED" for review in pr["latestOpinionatedReviews"]["nodes"]
    ):
        return "changes requested"
    if pr["reviewDecision"] == "REVIEW_REQUIRED" and approved_by(pr, viewer):
        return "needs another approval besides yours"
    checks = (head.get("statusCheckRollup") or {}).get("state")
    if checks != "SUCCESS":
        return f"checks {checks.lower()}" if checks else "no checks"
    if not own_check_passed(repository["nameWithOwner"], head["statusCheckRollup"]["contexts"]["nodes"]):
        return "no passing check from a workflow in this repository"
    if pr["mergeable"] != "MERGEABLE":
        return f"mergeable state {pr['mergeable'].lower()}"
    if pr["mergeStateStatus"] == "BEHIND":
        return "behind its base branch, which must be up to date"
    if not merge_method(repository):
        return "no merge method allowed"
    return None


def merge_method(repository):
    return next((method for flag, method in MERGE_METHODS if repository.get(flag)), None)


class GitHub:
    """Every call to GitHub goes through gh, signed in as the account that approves and merges."""

    def gh(self, args):
        try:
            result = subprocess.run(
                ["gh", *args], capture_output=True, text=True, timeout=GH_TIMEOUT_SECONDS, check=False
            )
        except subprocess.TimeoutExpired as error:
            raise GitHubError(f"gh {args[1]} timed out after {GH_TIMEOUT_SECONDS} seconds") from error
        if result.returncode != 0:
            raise GitHubError(f"gh {args[1]} failed: {result.stderr.strip()[-500:]}")
        try:
            return json.loads(result.stdout) if result.stdout.strip() else None
        except ValueError as error:
            raise GitHubError(f"gh {args[1]} returned invalid JSON") from error

    def graphql(self, query, fields):
        args = ["api", "graphql", "-f", f"query={query}"]
        for name, value in fields.items():
            args += ["-F" if isinstance(value, int) else "-f", f"{name}={value}"]
        data = self.gh(args)
        if not isinstance(data, dict) or data.get("errors") or not data.get("data"):
            errors = data.get("errors") if isinstance(data, dict) else data
            raise GitHubError(f"gh graphql failed: {json.dumps(errors)[:500]}")
        return data["data"]

    def search(self, query, cursor):
        return self.graphql(SEARCH_QUERY, {"q": query, **({"endCursor": cursor} if cursor else {})})

    def pull(self, repository, number):
        owner, name = repository.split("/")
        pr = self.graphql(PULL_QUERY, {"owner": owner, "name": name, "number": number})["repository"]["pullRequest"]
        if not pr:
            raise GitHubError(f"{repository}#{number} not found")
        return pr

    def approve(self, repository, number, sha):
        self.gh([
            "api", f"repos/{repository}/pulls/{number}/reviews", "-X", "POST",
            "-f", "event=APPROVE", "-f", f"commit_id={sha}", "-f", f"body={APPROVAL_BODY}",
        ])

    def merge(self, repository, number, sha, method):
        self.gh([
            "api", f"repos/{repository}/pulls/{number}/merge", "-X", "PUT",
            "-f", f"sha={sha}", "-f", f"merge_method={method}",
        ])


def log(**fields):
    print(json.dumps(fields, sort_keys=True), flush=True)


def open_pull_requests(github, owner):
    query = f"user:{owner} is:pr is:open author:app/dependabot archived:false"
    pulls, cursor, viewer = [], None, None
    while True:
        data = github.search(query, cursor)
        viewer = data["viewer"]["login"]
        pulls += [node for node in data["search"]["nodes"] if node]
        page = data["search"]["pageInfo"]
        if not page["hasNextPage"]:
            return viewer, sorted(pulls, key=lambda pr: pr["createdAt"])
        cursor = page["endCursor"]


def run(owner, dry_run, skip_repos=(), github=None):
    github = github or GitHub()
    skip_repos = {name.lower() for name in skip_repos}
    try:
        viewer, pulls = open_pull_requests(github, owner)
    except (GitHubError, KeyError, TypeError, ValueError) as error:
        log(owner=owner, action="failed", error=f"listing pull requests: {error}")
        return 1
    merged_repositories, failures, merged = set(), 0, 0
    for listed in pulls:
        approved, wrote = False, False
        try:
            repository = listed["repository"]["nameWithOwner"]
            if repository.split("/")[1].lower() in skip_repos:
                reason = "repository is on the skip list"
            else:
                reason = blockers(listed, viewer)
            if not reason and repository in merged_repositories:
                reason = "another update merged in this repository during this run"
            if reason:
                log(pr=listed["url"], action="skipped", reason=reason)
                continue
            # The listing can be minutes old, so check the pull request again right before writing.
            pr = github.pull(repository, listed["number"])
            reason = blockers(pr, viewer)
            if reason:
                log(pr=pr["url"], action="skipped", reason=f"changed since listing: {reason}")
                continue
            approve = pr["reviewDecision"] == "REVIEW_REQUIRED"
            method = merge_method(pr["repository"])
            if dry_run:
                log(pr=pr["url"], action="would_merge", approve=approve, method=method, head=pr["headRefOid"])
                merged_repositories.add(repository)
                continue
            # A write that fails may still have reached GitHub, for example on a timeout, so
            # the repository counts as handled for this run either way.
            wrote = True
            if approve:
                github.approve(repository, pr["number"], pr["headRefOid"])
                approved = True
            github.merge(repository, pr["number"], pr["headRefOid"], method)
        except (GitHubError, KeyError, TypeError, AttributeError, IndexError, ValueError) as error:
            failures += 1
            if wrote:
                merged_repositories.add(repository)
            log(pr=listed.get("url"), action="failed", approved=approved, error=f"{type(error).__name__}: {error}")
            continue
        merged += 1
        merged_repositories.add(repository)
        log(pr=pr["url"], action="merged", approved=approved, method=method, head=pr["headRefOid"])
    log(owner=owner, action="finished", dry_run=dry_run, open=len(pulls), merged=merged, failed=failures)
    return 1 if failures else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--owner", required=True, help="GitHub organization or user whose repositories to check")
    parser.add_argument("--dry-run", action="store_true", help="print what would merge without approving or merging")
    parser.add_argument(
        "--skip-repo", action="append", default=[], metavar="NAME",
        help="name of a repository under --owner to leave alone, such as one that deploys on every merge; repeatable",
    )
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})", args.owner):
        parser.error(f"--owner must be a GitHub organization or user name, not {args.owner!r}")
    for name in args.skip_repo:
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", name):
            parser.error(f"--skip-repo takes a repository name without its owner, not {name!r}")
    return run(args.owner, args.dry_run, args.skip_repo)


if __name__ == "__main__":
    sys.exit(main())
