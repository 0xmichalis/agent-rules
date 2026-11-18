from contextlib import redirect_stdout
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import unittest
import unittest.mock


spec = importlib.util.spec_from_file_location(
    "dependabot_merge",
    Path(__file__).resolve().parents[1] / "automations/dependabot-merge/dependabot_merge.py",
)
merge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge)

ME = "me-on-github"
HEAD = "a" * 40
SINGLE = """build(deps): bump rkyv from 0.8.15 to 0.8.16

Bumps [rkyv](https://github.com/rkyv/rkyv) from 0.8.15 to 0.8.16.
- [Release notes](https://github.com/rkyv/rkyv/releases)

---
updated-dependencies:
- dependency-name: rkyv
  dependency-version: 0.8.16
  dependency-type: indirect
...

Signed-off-by: dependabot[bot] <support@github.com>"""
GROUP = """build(deps): bump the circle-bridge group with 2 updates

Bumps the circle-bridge group with 2 updates: @circle-fin/adapter-viem-v2 and @circle-fin/bridge-kit.

Updates `@circle-fin/adapter-viem-v2` from 1.20.0 to 1.20.1
- [Commits](https://example.com)

Updates `@circle-fin/bridge-kit` from 1.17.0 to {kit}
- [Commits](https://example.com)

---
updated-dependencies:
- dependency-name: "@circle-fin/adapter-viem-v2"
  dependency-version: 1.20.1
  dependency-type: direct:production
  update-type: version-update:semver-patch
  dependency-group: circle-bridge
- dependency-name: "@circle-fin/bridge-kit"
  dependency-version: {kit}
  dependency-type: direct:production
  update-type: version-update:{kit_type}
  dependency-group: circle-bridge
...
"""
SUBJECT_ONLY = """Bump aiohttp from 3.13.4 to 3.14.3 in /analysis
---
updated-dependencies:
- dependency-name: aiohttp
  dependency-version: 3.14.3
  dependency-type: direct:production
...
"""


def commit(oid=HEAD, message=SINGLE, author=merge.DEPENDABOT_EMAIL, committer=merge.GITHUB_EMAIL,
           signed=True, checks="SUCCESS"):
    return {"commit": {
        "oid": oid, "message": message, "author": {"email": author}, "committer": {"email": committer},
        "signature": {"isValid": signed, "wasSignedByGitHub": signed},
        "statusCheckRollup": {"state": checks} if checks else None,
    }}


def pull(number=1, repo="Org/service", created="2026-11-01T00:00:00Z", **changes):
    pr = {
        "number": number, "url": f"https://github.com/{repo}/pull/{number}", "isDraft": False,
        "createdAt": created, "headRefOid": HEAD, "mergeable": "MERGEABLE", "mergeStateStatus": "BLOCKED", "reviewDecision": "REVIEW_REQUIRED",
        "author": {"login": "dependabot"},
        "repository": {
            "nameWithOwner": repo, "viewerPermission": "WRITE", "squashMergeAllowed": True,
            "mergeCommitAllowed": True, "rebaseMergeAllowed": True,
        },
        "latestOpinionatedReviews": {"nodes": []},
        "timelineItems": {"nodes": []},
        "commits": {"totalCount": 1, "nodes": [commit()]},
    }
    for key, value in changes.items():
        if key in pr["repository"]:
            pr["repository"][key] = value
        else:
            pr[key] = value
    return pr


def force_push(actor="dependabot", after=HEAD):
    return {"nodes": [{"__typename": "HeadRefForcePushedEvent", "actor": {"login": actor}, "afterCommit": {"oid": after}}]}


class FakeGitHub:
    def __init__(self, *pages, fail_merge=(), fail_search=False, fresh=None):
        self.pages = list(pages) or [[]]
        self.fail_merge = set(fail_merge)
        self.fail_search = fail_search
        # Pull requests as they look when checked again before writing, by number.
        self.fresh = fresh or {}
        self.calls = []

    def pull(self, repository, number):
        self.calls.append(("pull", repository, number))
        if number in self.fresh:
            return copy.deepcopy(self.fresh[number])
        return copy.deepcopy(next(
            pr for page in self.pages for pr in page
            if pr["repository"]["nameWithOwner"] == repository and pr["number"] == number
        ))

    def search(self, query, cursor):
        self.calls.append(("search", query, cursor))
        if self.fail_search:
            raise merge.GitHubError("gh graphql failed: HTTP 502")
        index = int(cursor or 0)
        last = index == len(self.pages) - 1
        return {
            "viewer": {"login": ME},
            "search": {
                "nodes": copy.deepcopy(self.pages[index]) + [{}],
                "pageInfo": {"hasNextPage": not last, "endCursor": None if last else str(index + 1)},
            },
        }

    def approve(self, repository, number, sha):
        self.calls.append(("approve", repository, number, sha))

    def merge(self, repository, number, sha, method):
        self.calls.append(("merge", repository, number, sha, method))
        if number in self.fail_merge:
            raise merge.GitHubError("gh api failed: Pull Request is not mergeable (HTTP 405)")


def run(github, dry_run=False, owner="Org"):
    output = io.StringIO()
    with redirect_stdout(output):
        code = merge.run(owner, dry_run, github=github)
    return code, [json.loads(line) for line in output.getvalue().splitlines()]


def writes(github):
    return [call for call in github.calls if call[0] not in ("search", "pull")]


class VersionTests(unittest.TestCase):
    def test_patch_and_minor_upgrades_pass(self):
        for old, new in [
            ("1.20.0", "1.20.1"), ("1.8.1", "1.18.0"), ("0.8.15", "0.8.16"), ("v4.2.0", "v4.3.0"),
            ("2026.7.22", "2026.10.19"), ("3.11", "3.15"), ("1.2", "1.2.1"),
        ]:
            with self.subTest(old=old, new=new):
                self.assertIsNone(merge.breaking_change(old, new))

    def test_major_upgrades_are_blocked_including_zero_major_minor_bumps(self):
        for old, new in [("6.1.0", "7.2.1"), ("0.8.15", "0.9.0"), ("0.0.3", "0.0.4"), ("1", "2")]:
            with self.subTest(old=old, new=new):
                self.assertIn("major update", merge.breaking_change(old, new))

    def test_downgrades_and_unrecognised_versions_are_blocked(self):
        self.assertIn("not an upgrade", merge.breaking_change("1.2.3", "1.2.3"))
        self.assertIn("not an upgrade", merge.breaking_change("1.3.0", "1.2.9"))
        for old, new in [("11bd719", "08c6903"), ("2.0.0", "2.1.0rc1"), ("3.12-slim", "3.13-slim"), ("1.0", "")]:
            with self.subTest(old=old, new=new):
                self.assertIn("unrecognised", merge.breaking_change(old, new))


class UpdateTests(unittest.TestCase):
    def test_single_group_and_subject_only_messages_pass(self):
        self.assertIsNone(merge.update_blocker(SINGLE))
        self.assertIsNone(merge.update_blocker(GROUP.format(kit="1.17.1", kit_type="semver-patch")))
        self.assertIsNone(merge.update_blocker(SUBJECT_ONLY))

    def test_one_major_update_blocks_a_group(self):
        self.assertEqual(
            merge.update_blocker(GROUP.format(kit="2.0.0", kit_type="semver-minor")),
            "@circle-fin/bridge-kit: major update 1.17.0 -> 2.0.0",
        )

    def test_dependabot_major_label_blocks_even_when_the_text_says_minor(self):
        self.assertEqual(
            merge.update_blocker(GROUP.format(kit="1.17.1", kit_type="semver-major")),
            "@circle-fin/bridge-kit: major update",
        )

    def test_missing_metadata_or_version_change_blocks(self):
        self.assertEqual(merge.update_blocker("Bump x from 1.0.0 to 1.0.1"), "commit message has no Dependabot metadata")
        without_change = SINGLE.replace("bump rkyv from", "bump rkyv-x from").replace("Bumps [rkyv]", "Bumps [other]")
        self.assertEqual(merge.update_blocker(without_change), "rkyv: version change not found in the commit message")

    def test_version_lines_after_the_metadata_are_ignored(self):
        message = SUBJECT_ONLY.replace("Bump aiohttp from 3.13.4 to 3.14.3", "Bump aiohttp") + (
            "\nUpdates `aiohttp` from 3.13.4 to 3.13.5\n"
        )
        self.assertEqual(merge.update_blocker(message), "aiohttp: version change not found in the commit message")


class BlockerTests(unittest.TestCase):
    def test_passing_pull_request_has_no_blocker(self):
        self.assertIsNone(merge.blockers(pull(), ME))

    def test_each_rule_blocks(self):
        cases = {
            "not opened by Dependabot": pull(author={"login": "teammate"}),
            "draft": pull(isDraft=True),
            "read access to the repository": pull(viewerPermission="READ"),
            "no access to the repository": pull(viewerPermission=None),
            "2 commits; only a single Dependabot commit is trusted": pull(commits={"totalCount": 2, "nodes": [commit()]}),
            "commit aaaaaaa is not a GitHub-signed Dependabot commit": pull(commits={"totalCount": 1, "nodes": [commit(signed=False)]}),
            "commit bbbbbbb is not a GitHub-signed Dependabot commit": pull(
                commits={"totalCount": 1, "nodes": [commit(oid="b" * 40)]}
            ),
            "branch was last rewritten by someone other than Dependabot": pull(timelineItems=force_push("teammate")),
            "changes requested": pull(reviewDecision="CHANGES_REQUESTED"),
            "checks failure": pull(commits={"totalCount": 1, "nodes": [commit(checks="FAILURE")]}),
            "checks pending": pull(commits={"totalCount": 1, "nodes": [commit(checks="PENDING")]}),
            "no checks": pull(commits={"totalCount": 1, "nodes": [commit(checks=None)]}),
            "mergeable state conflicting": pull(mergeable="CONFLICTING"),
            "behind its base branch, which must be up to date": pull(mergeStateStatus="BEHIND"),
            "no merge method allowed": pull(squashMergeAllowed=False, mergeCommitAllowed=False, rebaseMergeAllowed=False),
        }
        for reason, pr in cases.items():
            with self.subTest(reason=reason):
                self.assertEqual(merge.blockers(pr, ME), reason)

    def test_a_commit_from_someone_else_blocks_even_when_github_signed_it(self):
        pr = pull(commits={"totalCount": 1, "nodes": [commit(author="me@example.com")]})
        self.assertIn("not a GitHub-signed Dependabot commit", merge.blockers(pr, ME))
        pr = pull(commits={"totalCount": 1, "nodes": [commit(committer="me@example.com")]})
        self.assertIn("not a GitHub-signed Dependabot commit", merge.blockers(pr, ME))

    def test_only_a_dependabot_rebase_may_have_rewritten_the_branch(self):
        # A forged commit can carry Dependabot's author, GitHub's signature and a patch
        # message, as a squash merge does, but putting it on the branch needs a rewrite.
        self.assertIsNone(merge.blockers(pull(timelineItems=force_push()), ME))
        rewritten = "branch was last rewritten by someone other than Dependabot"
        for events in [
            force_push("teammate"),
            force_push(actor=None),
            force_push(after="e" * 40),
            {"nodes": [{"__typename": "HeadRefRestoredEvent"}]},
            {"nodes": [{"__typename": "HeadRefDeletedEvent"}]},
        ]:
            with self.subTest(events=events):
                self.assertEqual(merge.blockers(pull(timelineItems=events), ME), rewritten)

    def test_your_approval_at_the_head_that_is_not_enough_blocks(self):
        mine = {"state": "APPROVED", "author": {"login": ME.upper()}, "commit": {"oid": HEAD}}
        pr = pull(latestOpinionatedReviews={"nodes": [mine]})
        self.assertEqual(merge.blockers(pr, ME), "needs another approval besides yours")
        stale = dict(mine, commit={"oid": "d" * 40})
        self.assertIsNone(merge.blockers(pull(latestOpinionatedReviews={"nodes": [stale]}), ME))

    def test_merge_method_prefers_squash_then_merge_then_rebase(self):
        self.assertEqual(merge.merge_method(pull()["repository"]), "squash")
        self.assertEqual(merge.merge_method(pull(squashMergeAllowed=False)["repository"]), "merge")
        self.assertEqual(
            merge.merge_method(pull(squashMergeAllowed=False, mergeCommitAllowed=False)["repository"]), "rebase"
        )


class RunTests(unittest.TestCase):
    def test_searches_owner_and_pages_then_approves_and_merges_the_exact_head(self):
        github = FakeGitHub([pull(1)], [pull(2, repo="Org/infra", reviewDecision=None, squashMergeAllowed=False)])
        code, records = run(github)
        self.assertEqual(code, 0)
        self.assertEqual(
            [call[:3] for call in github.calls if call[0] == "search"],
            [("search", "user:Org is:pr is:open author:app/dependabot archived:false", None),
             ("search", "user:Org is:pr is:open author:app/dependabot archived:false", "1")],
        )
        self.assertEqual(writes(github), [
            ("approve", "Org/service", 1, HEAD),
            ("merge", "Org/service", 1, HEAD, "squash"),
            ("merge", "Org/infra", 2, HEAD, "merge"),
        ])
        self.assertEqual(records[-1], {
            "action": "finished", "dry_run": False, "failed": 0, "merged": 2, "open": 2, "owner": "Org",
        })

    def test_already_approved_pull_requests_merge_without_another_approval(self):
        github = FakeGitHub([pull(reviewDecision="APPROVED")])
        run(github)
        self.assertEqual(writes(github), [("merge", "Org/service", 1, HEAD, "squash")])

    def test_merges_the_oldest_update_and_only_one_per_repository(self):
        github = FakeGitHub([
            pull(2, created="2026-11-02T00:00:00Z"), pull(1, created="2026-11-01T00:00:00Z"),
            pull(3, repo="Org/infra", created="2026-11-03T00:00:00Z"),
        ])
        _, records = run(github)
        self.assertEqual([call[2] for call in writes(github) if call[0] == "merge"], [1, 3])
        skipped = [record for record in records if record["action"] == "skipped"]
        self.assertEqual(skipped, [{
            "action": "skipped", "pr": "https://github.com/Org/service/pull/2",
            "reason": "another update merged in this repository during this run",
        }])

    def test_dry_run_writes_nothing_and_reports_one_update_per_repository(self):
        github = FakeGitHub([pull(1), pull(2, created="2026-11-02T00:00:00Z"), pull(3, mergeable="CONFLICTING")])
        code, records = run(github, dry_run=True)
        self.assertEqual((code, writes(github)), (0, []))
        self.assertEqual([record["action"] for record in records], ["would_merge", "skipped", "skipped", "finished"])
        self.assertEqual(records[0]["approve"], True)

    def test_a_failed_merge_is_reported_and_the_run_continues_with_another_repository(self):
        github = FakeGitHub([pull(1), pull(2), pull(3, repo="Org/infra")], fail_merge={1})
        code, records = run(github)
        self.assertEqual(code, 1)
        self.assertEqual([call[2] for call in writes(github) if call[0] == "merge"], [1, 2, 3])
        failed = next(record for record in records if record["action"] == "failed")
        self.assertEqual((failed["pr"], failed["approved"]), ("https://github.com/Org/service/pull/1", True))
        self.assertEqual(records[-1]["merged"], 2)

    def test_a_pull_request_that_changed_since_listing_is_skipped(self):
        changed = pull(1, headRefOid="f" * 40, commits={"totalCount": 1, "nodes": [commit(oid="f" * 40, checks="PENDING")]})
        github = FakeGitHub([pull(1), pull(2, repo="Org/infra")], fresh={1: changed})
        code, records = run(github)
        self.assertEqual(code, 0)
        self.assertIn(("pull", "Org/service", 1), github.calls)
        self.assertEqual(writes(github), [("approve", "Org/infra", 2, HEAD), ("merge", "Org/infra", 2, HEAD, "squash")])
        self.assertEqual(records[0], {
            "action": "skipped", "pr": "https://github.com/Org/service/pull/1",
            "reason": "changed since listing: checks pending",
        })

    def test_unexpected_data_fails_one_pull_request_and_the_run_continues(self):
        broken = pull(1)
        del broken["timelineItems"]
        github = FakeGitHub([broken, pull(2, repo="Org/infra")])
        code, records = run(github)
        self.assertEqual(code, 1)
        self.assertEqual(records[0]["action"], "failed")
        self.assertTrue(records[0]["error"].startswith("KeyError"))
        self.assertEqual(writes(github)[-1], ("merge", "Org/infra", 2, HEAD, "squash"))

    def test_a_failed_approval_is_not_reported_as_approved(self):
        github = FakeGitHub([pull(1)])
        github.approve = unittest.mock.Mock(side_effect=merge.GitHubError("gh api failed: HTTP 422"))
        code, records = run(github)
        self.assertEqual((code, records[0]["action"], records[0]["approved"]), (1, "failed", False))

    def test_a_failed_search_fails_the_run_without_writes(self):
        github = FakeGitHub(fail_search=True)
        code, records = run(github)
        self.assertEqual((code, writes(github)), (1, []))
        self.assertEqual(records, [{
            "action": "failed", "owner": "Org", "error": "listing pull requests: gh graphql failed: HTTP 502",
        }])


class GitHubTests(unittest.TestCase):
    def completed(self, stdout="", returncode=0, stderr=""):
        return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr=stderr)

    def test_approval_and_merge_are_pinned_to_the_head_commit(self):
        with unittest.mock.patch.object(merge.subprocess, "run", return_value=self.completed("{}")) as runner:
            merge.GitHub().approve("Org/service", 7, HEAD)
            merge.GitHub().merge("Org/service", 7, HEAD, "squash")
        approve, put = (call.args[0] for call in runner.call_args_list)
        self.assertEqual(approve[:5], ["gh", "api", "repos/Org/service/pulls/7/reviews", "-X", "POST"])
        self.assertIn(f"commit_id={HEAD}", approve)
        self.assertIn("event=APPROVE", approve)
        self.assertEqual(put[:5], ["gh", "api", "repos/Org/service/pulls/7/merge", "-X", "PUT"])
        self.assertIn(f"sha={HEAD}", put)
        self.assertIn("merge_method=squash", put)

    def test_gh_failures_graphql_errors_and_timeouts_raise_github_errors(self):
        outcomes = [
            self.completed(returncode=1, stderr="HTTP 405: Pull Request is not mergeable"),
            self.completed(json.dumps({"errors": [{"message": "Something went wrong"}]})),
            self.completed(json.dumps({"data": None})),
            self.completed("<html>502 Bad Gateway</html>"),
            subprocess.TimeoutExpired(["gh"], 120),
        ]
        for outcome in outcomes:
            with self.subTest(outcome=type(outcome).__name__), unittest.mock.patch.object(
                merge.subprocess, "run", side_effect=[outcome]
            ):
                with self.assertRaises(merge.GitHubError):
                    merge.GitHub().search("user:Org", None)

    def test_search_passes_the_cursor_only_after_the_first_page(self):
        reply = json.dumps({"data": {"viewer": {"login": ME}, "search": {}}})
        with unittest.mock.patch.object(merge.subprocess, "run", return_value=self.completed(reply)) as runner:
            merge.GitHub().search("user:Org", None)
            merge.GitHub().search("user:Org", "Y3Vyc29y")
        first, second = (call.args[0] for call in runner.call_args_list)
        self.assertFalse(any(arg.startswith("endCursor=") for arg in first))
        self.assertEqual(second[-2:], ["-f", "endCursor=Y3Vyc29y"])

    def test_pull_reads_one_pull_request_with_a_numeric_number(self):
        reply = json.dumps({"data": {"repository": {"pullRequest": {"number": 7}}}})
        with unittest.mock.patch.object(merge.subprocess, "run", return_value=self.completed(reply)) as runner:
            self.assertEqual(merge.GitHub().pull("Org/service", 7), {"number": 7})
        args = runner.call_args.args[0]
        self.assertEqual(args[-6:], ["-f", "owner=Org", "-f", "name=service", "-F", "number=7"])
        missing = json.dumps({"data": {"repository": {"pullRequest": None}}})
        with unittest.mock.patch.object(merge.subprocess, "run", return_value=self.completed(missing)):
            with self.assertRaises(merge.GitHubError):
                merge.GitHub().pull("Org/service", 7)


class MainTests(unittest.TestCase):
    def test_owner_must_be_a_github_name(self):
        for owner in ["Org/repo", "-org", "org name", "a" * 40]:
            with self.subTest(owner=owner), redirect_stdout(io.StringIO()), unittest.mock.patch("sys.stderr", io.StringIO()):
                with self.assertRaises(SystemExit):
                    merge.main(["--owner", owner])

    def test_main_passes_owner_and_dry_run(self):
        with unittest.mock.patch.object(merge, "run", return_value=0) as runner:
            self.assertEqual(merge.main(["--owner", "ExampleOrg", "--dry-run"]), 0)
        runner.assert_called_once_with("ExampleOrg", True)


if __name__ == "__main__":
    unittest.main()
