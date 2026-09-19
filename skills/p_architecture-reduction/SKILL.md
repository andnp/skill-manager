---
name: p_architecture-reduction
description: "Audit and refactor an owned codebase for net-negative code volume, escalating from dead code to architectural, algorithmic, and data-structure simplification with evidence and validation. Invoke only when explicitly requested by name; do not self-trigger."
invocation: manual
---

# Architecture Reduction

Use this skill when the user wants a codebase slimmer, simpler, more modular, or more reusable. The outcome is a validated sequence of behavior-preserving changes with more code deleted than added whenever the repository permits it.

Apply the `architecture-knowledge` skill's core standard and leverage taxonomy throughout this audit rather than re-deriving them here.

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

Classify each finding using `architecture-knowledge`'s leverage taxonomy (literal dead code, redundancy, boundary simplification, problem reframing) rather than by file type. When duplication is the primary complaint, or a candidate's implementations look different but may answer the same requirement or encode the same truth, use the `duplication-diagnostics` skill for the escalation ladder and diagnostic before ranking it here.

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
