---
name: fix-ci-failures
description: "Use when triaging CI failures, red builds, failing checks, broken GitHub Actions runs, post-push verification failures, flaky-or-real check investigation, and same-branch/worktree GitHub Actions debugging with gh CLI logs and reruns."
---

# Fix CI Failures

Use this skill when a branch or PR has failing CI. Treat the skill as the repeatable workflow and memory as the place to retrieve and update the real debugging rules.

## Operating rules

1. Search memory first for repo verification preferences, prior failure modes, debugging lessons, and task-specific context when memory is available. Otherwise use the context and evidence available in the current task; never invent prior lessons.
2. Stay on the existing issue branch and worktree when one exists. Do not create a new branch or worktree solely for CI follow-up.
3. Prefer `gh` CLI to inspect checks, workflow runs, job logs, and rerun state. If it is unavailable, say what evidence is missing and use the available local logs or provider output.
4. Once the root cause is known, record one durable memory thought when memory is available, capturing the failure mode, detection path, and reusable debugging lesson.

## Workflow

1. Establish the repository, branch, PR or issue, and failing check. If no PR exists, inspect runs for the current branch.
2. Determine which job actually failed and pull the relevant failed-job logs.
3. Distinguish failed, canceled, queued, flaky, and infrastructure failures before editing.
4. Map the failing check to the closest local reproduction command and reproduce locally whenever feasible.
5. Make the smallest correct fix on the same branch/worktree.
6. Run the narrowest local verification that proves the failure is fixed.
7. Push the existing branch.
8. Re-check GitHub status with `gh pr checks` or `gh run list`/`gh run view` until the relevant signal is green or a new blocker is identified.

## Triage guidance

- Distinguish root cause from noisy downstream failures before editing.
- Prefer exact failing-job logs over broad guesswork.
- Capture the check-to-command mapping explicitly so local verification matches CI reality.
- If the failure came from environment drift, dependency mismatch, or identity/auth issues, record that in memory as part of the reusable lesson.
- If checks are queued, canceled, or unavailable, report that state instead of treating it as a code failure.

## References

- `references/gh-cli-ci-playbook.md` - command patterns for reading checks, reproducing locally, and re-checking after a push.
