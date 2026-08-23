---
name: architecture-reduction
description: "Audit and refactor an owned codebase for net-negative code volume, escalating from dead code to architectural, algorithmic, and data-structure simplification with evidence and validation."
---

# Architecture Reduction

Use this skill when the user wants a codebase slimmer, simpler, more modular, or more reusable. The outcome is a validated sequence of behavior-preserving changes with more code deleted than added whenever the repository permits it.

## Core standard

Dream big. Dead-code removal is the lowest level of achievement, not the goal.

For every subsystem, ask whether a better representation or design could remove whole families of code:

- Can one capability-oriented boundary replace an oversized repository or service?
- Can a generic engine replace several nearly identical workflows?
- Can an index, cache, memoized representation, or incremental algorithm replace repeated full scans?
- Can a registry, schema, pipeline, or state machine replace branching and hand-written dispatch?
- Are multiple models or adapters translating between equivalent shapes?
- Can a canonical data structure make downstream code trivial?
- What would a 10x simpler design look like, and what evidence would make it safe to adopt?

Do not add abstraction for its own sake. Prefer changes that reduce conceptual paths, coupling, maintenance surface, or repeated work in addition to reducing LOC.

## 1. Establish evidence

Inspect before editing. Read repository-local instructions, configuration, architecture documentation, entrypoints, tests, and relevant history. Preserve unrelated user or agent changes.

Record a baseline for the repository where practical:

- source and test LOC
- branch and worktree state
- test count and runtime
- lint and type-check status
- architecture/import-contract status
- known failures and environment limitations

Use symbol/caller/import tools or indexed repository tools when available. Use `rg`, AST inspection, and direct file reads for configuration, scripts, and gaps in indexed context.

## 2. Build an opportunity ledger

Classify findings by leverage rather than by file type:

1. Literal dead code: unused settings, orphan modules, stale exports, unreachable aliases, and obsolete compatibility paths.
2. Redundancy: forwarding facades, duplicate helpers, repeated fallback paths, and equivalent model translations.
3. Boundary simplification: oversized repositories, unclear ownership, dynamic seams, and duplicated orchestration.
4. Problem reframing: algorithms, data structures, indexes, registries, pipelines, state machines, or incremental computation that could eliminate large regions of code.

For every candidate, capture:

- exact files and symbols
- caller, entrypoint, test, and configuration evidence
- behavior and compatibility risk
- expected additions and deletions
- before/after conceptual complexity
- recommended implementation boundary
- confidence and unresolved questions

Never call code dead solely because a simple text search found no caller. Check runtime entrypoints, dynamic access, external boundaries, fixtures, and contracts.

## 3. Orchestrate bounded work

Use explorers for independent, read-heavy investigations and workers for bounded implementation. Run agents sequentially unless their write sets are genuinely disjoint.

Every implementation proposal must include:

- conventional commit subject and why
- owned files and explicit non-owned files
- expected LOC delta
- behavior and migration strategy
- tests and validation commands
- risks, stop conditions, and follow-up opportunities

Do not let subagents commit. The main agent owns approval, sequencing, integration, and final verification. For multi-commit work, agree the commit sequence before implementation; each commit must be independently valid and as small as the dependency structure allows.

When the worktree is shared, stage only explicit owned paths and check the staged file list immediately before committing. If concurrent work may affect hooks or branch state, validate the exact patch in a clean worktree based on the latest parent before integration. Never use broad staging or destructive branch-reset commands to resolve interference.

## 4. Implement canonical replacements

For an accepted change:

- migrate all owned callers to one canonical path
- remove the superseded implementation in the same coherent slice
- remove stale tests, exports, settings, aliases, and compatibility scaffolding
- avoid parallel old/new implementations unless rollout or backward compatibility is explicitly required
- keep behavior contracts stable unless the user asked for a behavior change
- add abstractions only when they eliminate more complexity than they introduce

Start with high-confidence deletions when useful, then use the simplified design to unlock larger structural changes. Do not stop after deleting a few symbols if the evidence points to a larger architectural reduction.

## 5. Review and validate

Use an independent reviewer for cross-layer changes, repository/port migrations, dynamic import changes, algorithmic rewrites, and other high-risk slices. Give the reviewer a narrow question and concrete acceptance criteria.

For each slice, inspect the exact diff and run the narrowest useful checks first:

- stale-reference and zero-caller scans
- architecture and import-contract tests
- focused behavior tests
- repository lint and type checks
- full tests when runtime or integration behavior is affected

Run the repository's established checks across the whole repository when relevant. Never hide failures with `--no-verify`; distinguish baseline failures from regressions and report both.

Measure the owned changes explicitly. Report additions, deletions, net LOC, conceptual simplifications, validation results, and deferred opportunities. A successful pass ends with a clean worktree or a precise accounting of unrelated work that was preserved.
