---
name: delegate-code-review
description: "Use only to obtain an independent outside opinion through the external agy CLI with Gemini's heavy reasoning tier. Do not use it to orchestrate built-in subagents. Trigger after producing a complex implementation plan, moderate-to-complex code, or high-risk code, or when the user explicitly asks Gemini to review a plan, code, implementation, diff, or similar work. For other direct review requests, use the normal review workflow."
---

# Delegate Code Review

Use this skill only to obtain an independent outside opinion from Gemini through the external `agy` CLI. It is an advisory review mechanism, not a general delegation or subagent-orchestration mechanism.

If the task calls for splitting work among the harness's built-in subagents, use the built-in subagent mechanism (or the `sub` skill) instead. Do not invoke this skill merely because another agent should do work; invoke it when an external review is useful or explicitly requested.

## Trigger boundary

Invoke implicitly when at least one of these is true and an outside opinion would help:

- The agent has produced a plan with multiple dependent steps, architectural choices, migrations, security implications, or a meaningful compatibility risk.
- The agent has written or substantially changed moderate-to-complex code.
- The agent has changed high-risk code: authentication, authorization, data loss or migration paths, concurrency, persistence, networking, sandboxing, secrets, deployment, or safety controls.
- The user explicitly asks to “ask Gemini” (or equivalent) to review a plan, code, implementation, diff, or similar artifact.

Do not invoke it merely because a change has multiple files, adds boilerplate, needs ordinary lint/test cleanup, or should be delegated to a built-in subagent. For direct review requests, use this skill only when the user explicitly names Gemini or asks for an external reviewer; otherwise use the normal review workflow.

## Workflow

1. Finish enough of the plan or implementation that a reviewer can assess a concrete artifact. Do not ask for a review of an intention that has no proposed steps, code, diff, or verification strategy.
2. Gather only task-local context: the goal, constraints, relevant prior decisions, changed files or proposed file boundaries, the plan or diff, and checks already run. Prefer a focused diff plus the surrounding symbols over an entire repository dump.
3. Build the prompt using the template below. State whether this is a `plan` or `implementation` review and what decisions are already settled.
4. Run the external review with the heavy installed Gemini tier:

   ```sh
   agy --model gemini-3.7-flash-high --effort high -p "<review prompt>" --print-timeout 600s
   ```

   `--print-timeout` uses a 10-minute default (`600s`) and requires a unit-suffixed duration; a bare number is rejected.
   Use `gemini-3.7-flash-high`, not the unsuffixed `gemini-3.7-flash`: the installed heavy model identifier is what ensures the requested reasoning tier. If `agy` rejects that identifier, inspect `agy models` and report the missing capability rather than silently using a lower tier.
   If headless mode denies a repository-read tool because it cannot prompt for command permission, rerun with an explicitly approved headless permission mode (e.g. `--dangerously-skip-permissions`) for a read-only review, or fall back to an evidence-only prompt that requires no tool use — never silently downgrade the model or skip the review.
   Retain the conversation ID reported by `agy`; it is needed for reliable follow-up.
5. Continue the same external review when a second review or iteration is useful:

   ```sh
   agy --conversation "<conversation-id>" --model gemini-3.7-flash-high --effort high -p "<follow-up with the new diff, findings, or question>" --print-timeout 600s
   ```

   Use the same conversation for follow-up findings, revised plans, or questions about a proposed correction. For an interactive iteration, use `-i` instead of `-p`. Use `agy --continue` only when this is definitely the most recent relevant Agy conversation; prefer `--conversation` when other Agy sessions may have run. A continuation is still an external Gemini review, not delegation to a built-in subagent.
6. Read the result critically. Verify every finding against the current files, requirements, and tests. Apply only findings that are real, in scope, and consistent with settled decisions; report rejected suggestions when they would cause scope creep or contradict a constraint.
7. If the review finds a blocking issue, fix it and rerun the narrowest relevant checks. If the review is clean, continue with normal verification and state that an independent review was run.

## Prompt construction

Write the prompt for a capable reviewer with no conversation history. Include:

- **Role and task:** “Act as an independent senior reviewer. Review the proposed plan/implementation for correctness and risk; do not implement changes.”
- **Success criteria:** the user-visible goal, invariants, compatibility promises, and acceptance checks.
- **Scope:** repository/worktree, relevant file paths, symbols, plan or diff, and any important call paths or data shapes.
- **Known decisions:** choices already made, explicit non-goals, and constraints. Ask the reviewer to flag risks without reopening settled choices unless they create a concrete correctness or safety problem.
- **Review lens:** the targeted risks below, selected for the artifact instead of pasted indiscriminately.
- **Output contract:** findings first, each with severity, evidence, impact, and a minimal correction; then missing tests or verification and a short residual-risk summary.

For a plan review, emphasize missing dependency ordering, unstated assumptions, migration/rollback safety, ownership boundaries, failure behavior, and whether the verification plan can actually prove the change. For an implementation review, emphasize behavioral regressions, contract violations, boundary conditions, state transitions, data integrity, concurrency, authorization, and tests that fail to exercise the changed behavior.

Use this compact prompt shape:

```text
You are an independent senior reviewer. Review this <plan|implementation> for the goal below.
Do not edit files, redesign settled decisions, or give generic style advice.

Goal and acceptance criteria:
<...>

Constraints, settled decisions, and non-goals:
<...>

Artifact under review:
<plan, diff, relevant files/symbols, and verification already run>

Focus only on risks relevant to this artifact:
<selected review lenses>

Return:
1. Findings ordered by severity: blocker, high, medium, low. For each: location, concrete evidence, impact, and smallest safe correction.
2. Missing or misleading verification.
3. Residual risks and assumptions.
If there are no actionable findings, say so and name the most important area you checked.
```

## Review philosophies

Prefer findings that protect these properties:

- **Smallest correct change:** reject speculative abstractions, broad rewrites, and compatibility layers without a demonstrated caller or requirement.
- **Invariant before happy path:** check what must remain true across retries, partial failure, empty input, cancellation, restart, and rollback—not just the nominal example.
- **Boundaries are contracts:** scrutinize serialization, CLI/API inputs, permissions, subprocesses, network responses, persistence, and version boundaries for explicit validation and safe failure.
- **State transitions must be observable:** look for illegal intermediate states, duplicate effects, lost updates, and cleanup that is skipped on error.
- **Tests should prove behavior:** prefer a test that would fail for the reported regression over coverage of implementation details or a snapshot that can pass while the contract is broken.
- **Verification must match risk:** a plan that changes a security or data boundary needs a targeted proof, not only formatting, type, or happy-path checks.

The external reviewer is advisory. Do not accept a finding solely because it sounds plausible; confirm the location, reproduce the behavior when practical, and preserve the user's scope.
