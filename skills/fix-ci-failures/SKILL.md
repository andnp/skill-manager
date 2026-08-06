---
name: fix-ci-failures
description: "Use when triaging CI failures, red builds, failing checks, broken GitHub Actions runs, post-push verification failures, flaky-or-real check investigation, and same-branch/worktree GitHub Actions debugging with gh CLI logs and reruns."
---

# Fix CI Failures

Use this skill when a branch or PR has failing CI. Treat the skill as the repeatable workflow and memory as the place to retrieve and update the real debugging rules.

## Required operating rules

1. Search memory first for repo verification preferences, prior failure modes, debugging lessons, and task-specific context.
2. Read the full relevant memory records before acting.
3. Stay on the existing issue branch and existing worktree for CI follow-up. Do not create a new branch or worktree just to fix failing checks.
4. Prefer `gh` CLI to inspect checks, workflow runs, job logs, and rerun state.
5. Once the root cause is known, record a durable memory thought capturing the failure mode, how it was detected, and the reusable debugging lesson.

## Workflow

1. Identify the failing PR/check context with `gh pr checks`, `gh run list`, and `gh run view`.
2. Determine which job actually failed and pull the relevant failed-job logs.
3. Map the failing check to the closest local reproduction command.
4. Reproduce locally before editing whenever feasible.
5. Make the smallest correct fix on the same branch/worktree.
6. Run the narrowest local verification that proves the failure is fixed.
7. Push the existing branch.
8. Re-check GitHub status with `gh pr checks` or `gh run list`/`gh run view` until the relevant signal is green or a new blocker is identified.

## Triage guidance

- Distinguish root cause from noisy downstream failures before editing.
- Prefer exact failing-job logs over broad guesswork.
- Capture the check-to-command mapping explicitly so local verification matches CI reality.
- If the failure came from environment drift, dependency mismatch, or identity/auth issues, record that in memory as part of the reusable lesson.

## References

- `references/gh-cli-ci-playbook.md` - command patterns for reading checks, reproducing locally, and re-checking after a push.