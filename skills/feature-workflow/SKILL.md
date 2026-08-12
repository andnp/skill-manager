---
name: feature-workflow
description: "Plan and implement repository feature work with an evidence-based refactor decision before coding. Use when adding a feature, extending an existing capability, or making a cross-cutting behavior change; allow a simple feature to proceed without refactoring when the current design is adequate."
---

> make the change easy, then make the easy change

# Feature Workflow

Use this skill to turn a feature request into a safe, reviewable implementation. Treat the mantra as a decision principle, not a requirement to refactor every task: remove concrete design friction when doing so materially reduces implementation risk, then implement the feature through the resulting seam.

## Operating rules

- Inspect before changing anything. Read repository instructions, configuration, entry points, relevant callers, and nearby tests.
- Preserve unrelated user changes and determine the repository's source-of-truth boundaries before editing.
- Search project memory when available; read relevant records fully before relying on them.
- Read and follow the repository's commit-planning skill before writing code when one is available.
- Test behavior and contracts rather than implementation details. Use the repository's existing test and type-checking conventions.
- Never introduce a speculative abstraction, compatibility layer, migration, or error path without concrete task-local evidence.
- When the feature migrates callers onto a dependency's new API, verify the API is actually published in the locked/installed version (not just present in the dependency's own working tree) before migrating consumer code.

## Workflow

### 1. Establish the feature contract

Write down the requested behavior, affected users or systems, explicit non-goals, constraints, and acceptance criteria. Resolve ambiguity from current code, configuration, documentation, and history before inventing requirements.

Identify:

- the externally observable behavior that must change;
- the current owner of that behavior;
- callers, consumers, persistence, integrations, and runtime entry points;
- normal, boundary, and failure cases that must remain safe;
- the narrowest verification that can prove the change.

For a very small, localized feature, keep this assessment brief. Do not create an architecture exercise where a direct change is already safe.

### 2. Inspect the current design

Use fast repository search and the project's architecture tools when available. Follow the behavior from entry point to implementation and callers. Look for concrete friction rather than aesthetic preferences:

- duplicated policy or protocol handling;
- configuration or endpoint logic embedded in domain methods;
- a missing seam that forces unrelated callers to change;
- difficult or brittle test setup;
- multiple runtime construction paths that would otherwise drift;
- a coupling that makes rollback, verification, or ownership unclear.

Verify architectural findings against current files. A symbol count or search result is evidence to investigate, not a refactoring mandate.

### 3. Make the refactor decision

Record exactly one outcome:

#### No refactor needed

Choose this when the feature is localized, the existing seam is adequate, or the proposed refactor would be speculative, aesthetic, or larger than the feature. State the reason, then implement the simplest safe change.

#### Targeted refactor

Choose this when one small behavior-preserving seam will materially reduce caller churn, risk, duplication, or test complexity. Define the seam, its payoff, and a stopping condition before editing.

#### Larger refactor required

Choose this only when the current design makes the feature unsafe, untestable, or disproportionately expensive. Split the work into independently valid slices, call out the added risk, and seek explicit agreement when the refactor expands beyond the feature's natural ownership boundary.

Use this decision record:

```text
Refactor decision: none | targeted | larger
Concrete friction:
Proposed seam or reason to keep the current design:
Expected payoff:
Scope:
Stopping condition:
```

Use these escape hatches deliberately:

- A one-file or one-function feature may use `none` without a lengthy architecture analysis.
- If an existing abstraction already owns the behavior, extend it instead of adding another layer.
- If the refactor cannot be justified by a concrete current obstacle, defer it.
- If the refactor touches unrelated APIs, schemas, deployment systems, or ownership boundaries, split the work or stop for direction.
- If the refactor's stopping condition cannot be stated, do not start it.

### 4. Plan independently valid work

Plan the implementation before editing. Prefer this ordering when a targeted refactor is selected:

1. Add or clarify the seam without changing observable behavior.
2. Add focused contract or parity tests for the seam.
3. Implement the feature through the seam.
4. Add feature-specific tests and documentation.
5. Remove obsolete paths only when the feature makes them unnecessary and evidence supports deletion.

Keep refactor and feature commits separate unless separating them would create a broken intermediate state. Each commit must compile, lint, pass its relevant tests, and be bisect-safe. Follow the repository's atomic commit and absorption rules.

### 5. Execute the refactor, if selected

Keep the refactor behavior-preserving:

- preserve public contracts, output shapes, ordering, side effects, and failure semantics;
- migrate owned callers to the canonical seam rather than adding a forwarding facade;
- avoid unrelated cleanup;
- run focused checks before adding feature behavior;
- stop when the recorded stopping condition is met.

If verification shows that the seam is not reducing the concrete friction, revert the refactor plan and take the direct implementation path rather than expanding the abstraction.

### 6. Implement the feature

Make the smallest change that satisfies the contract. Keep policy in the owning layer, keep integrations behind explicit ports or sessions where the refactor established them, and avoid pushing task-specific branching into unrelated callers.

Add tests for meaningful normal, boundary, and failure behavior. Prefer real implementations or focused fakes over broad mocks. Keep tests deterministic and resilient to internal rearrangement.

### 7. Verify proportionally

Run the narrowest relevant checks first, then widen them according to impact:

- formatter/linter/type checks required by the repository;
- focused unit or contract tests;
- integration, API, storage, daemon, or deployment checks when those boundaries changed;
- the default repository suite for cross-cutting changes.

For runtime or external-system changes, perform a safe smoke test and verify logs, health, and the actual execution path together. Do not infer runtime success from a shallow endpoint check alone.

### 8. Close the loop

Report:

- the feature outcome;
- the refactor decision and why it was or was not needed;
- changed files and ownership boundaries;
- verification performed and any uncertainty;
- follow-up work that was deliberately deferred;
- durable findings, failure modes, or reusable patterns worth recording in memory.

## Completion standard

Finish with the simplest canonical design that safely supports the feature. A successful run may include no refactor at all. When a refactor is included, it must have removed named friction, stayed within its declared scope, and left the feature implementation smaller or safer than the direct alternative.
