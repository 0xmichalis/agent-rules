# Operations and documentation

* Prefer existing Compose services for local dependencies. Use dedicated test
  databases and volumes; never destroy existing user data to obtain a clean run.
  Track owned processes and stop them gracefully before escalating termination.
* Provide complete commands with known inputs filled in. Use native directory
  flags or absolute paths, one command per fenced block, without chained steps
  or unnecessary setup. Include actual prerequisites. In shared text, use paths
  relative to the repository root and say to run from there, never a
  workstation-specific path.
* Group multi-environment procedures by environment: complete staging and its
  verification before production. State what success looks like.
* For Terraform, give each stack's init, plan with `-out`, and saved-plan apply
  separately, written out in full with `-chdir` and the stack's path from the
  repository root, in PR descriptions too.
  Never one templated command set with a stack placeholder. Inspect the plan
  before applying; honor project-specific execution permissions and refresh
  behavior. Never assume planning has no side effects.
* Use the appropriate CLI for a one-off operational action rather than adding
  temporary deployment flags. Permanent managed resources and repeatable
  workflows stay in the owning configuration. Record consequential operations.
* Re-read a target after an edit conflict before retrying. Preserve concurrent
  changes. Minimize and batch external API calls without sacrificing correctness.
* Keep runbooks to actions, checks, values and direct resource links. Reference
  the owning registry for values that change rather than copying them everywhere.
* Documentation and comments describe current behavior. Put ticket history in
  PRs and commits. External derivatives of reports preserve the source's scope,
  findings and criteria; distinguish additional analysis explicitly.
