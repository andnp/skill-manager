## gh CLI workflow for CI triage

1. Establish context with `gh pr view <number>` or the current branch name.
2. Use `gh pr checks <number>` for a pull request, or `gh run list --branch <branch>` when no pull request exists.
3. Read the relevant run with `gh run view <run-id>` and failed-job output with `gh run view <run-id> --log-failed`.
4. Classify the signal as failed, canceled, queued, flaky, or infrastructure-related before editing.
5. Map each failing check to the nearest local command and reproduce it when feasible.
6. After the fix and existing branch push, re-check with `gh pr checks <number>` or `gh run view <run-id>`.
