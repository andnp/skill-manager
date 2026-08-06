## gh CLI workflow for CI triage

- Start with `gh pr checks <number>` to see which checks failed.
- Inspect recent runs with `gh run list --branch <branch>`.
- Read failed-job output with `gh run view <run-id> --log-failed`.
- Map each failing check to the nearest local command and run that locally before changing code when feasible.
- Keep fixes on the same branch/worktree, push, then re-check status with `gh pr checks <number>` or `gh run view <run-id>`.
- After the root cause is known, record one durable memory that captures the failure mode, detection path, and reusable debugging lesson.