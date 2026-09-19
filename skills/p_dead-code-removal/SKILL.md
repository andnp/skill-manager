---
name: p_dead-code-removal
description: "Audit and remove literal dead code, obsolete compatibility shims, legacy-shaped facades, redundant defensive branches, stale exports, and duplicated fallback paths. Use when slimming an owned application or library, retiring a migration layer, deleting unused symbols, simplifying an architecture, or separating necessary resilience from conceptual dead code. Invoke only when explicitly requested by name; do not self-trigger."
invocation: manual
---

# Dead Code Removal

Use this skill to make a repository smaller by evidence, not by deleting every
symbol whose name contains `legacy`, `compat`, `fallback`, or `deprecated`.

Before classifying any candidate, load the `dead-code-knowledge` skill for the
evidence taxonomy (dead symbol / pure forwarding re-export / owned
compatibility layer / conceptually dead behavior / live migration-or-resilience
behavior) and the general operating stance on names-as-clues, re-export
anti-patterns, and fallback evidence. This skill covers the procedure around
that taxonomy: scoping an audit, building an evidence ledger, sequencing
commits, and verifying a deletion.

## Operating stance

- Inspect repository instructions, package metadata, entry points, and current
  worktree state before changing anything.
- Search project memory first when memory tooling is available; read relevant
  records fully before relying on them.
- Assume a GitHub flow branching model (short-lived feature branches with single
  ownership; `main`/`master` is the shared integration branch). Any lint error,
  type mismatch, broken assertion, or bug introduced anywhere within the active
  feature branch (when on a branch other than `main`/`master`) must be absorbed
  or corrected directly into the feature branch commit that introduced it
  (using `git commit --amend`, `git rebase -i`, or `but absorb`). Never create
  separate fixup commits or leave dirty correction patches for errors introduced
  within the active feature branch.
- Preserve unrelated user changes. Never reset a dirty worktree to make the
  audit easier.

## Automated language-specific tools

Use language-specific dead code tools to generate candidate lists for the evidence ledger. Automated tools accelerate discovery but require verification against dynamic access, plugin mechanisms, or entry points before deletion.

### Python
- `uv tool run deadcode .` — Scans Python AST to detect uncalled functions, classes, and variables.
- `uv tool run vulture .` — Static analysis for unused Python code with confidence scoring.
- `uv run ruff check --select F401,F841 .` — Fast linting for unused imports (`F401`) and unused local variables (`F841`).

### TypeScript / JavaScript
- `npx knip` — Scans for unused files, unused exports, unused types, unused dependencies, and circular references.
- `npx ts-prune` — Identifies unused `export` statements in TypeScript projects.

*(Expandable for additional languages like Rust, C++, Go as tools are adopted.)*

## Workflow

### 1. Establish scope

Read `AGENTS.md`, project configuration, package metadata, deployment files,
and the nearest tests. Determine whether the repository is an owned application,
a library with external consumers, or a mixed system. Check:

- package exports and entry points;
- CLI commands, MCP/tool registrations, plugin registries, and serializers;
- dynamic imports, reflection, dependency injection, and subprocess calls;
- scripts, configuration, templates, migrations, and documentation examples;
- generated files and source-of-truth boundaries.

Run the repository's status command once and preserve unrelated changes.

### 2. Build an evidence ledger

For each candidate, record:

| Candidate | Kind | Callers | Canonical replacement | Protected behavior | Decision |
| --- | --- | --- | --- | --- | --- |

Classify `Kind` using the `dead-code-knowledge` taxonomy. Use `rg`/`rg --files`
first. Use `repowise` or an equivalent symbol/caller tool when available for
architecture questions, then verify findings against files. Search names,
import paths, constructor calls, string registrations, config keys, and
serialized field names. A zero textual match is not enough when reflection or
plugin discovery exists.

Useful starting searches include:

```bash
rg -n '(compat|compatib|legacy|deprecated|shim|facade|adapter|wrapper|alias|fallback)' .
rg -n '__all__|entry_points|import_module|getattr\(|hasattr\(|register|plugin' .
rg -n 'from .* import \*|^\s*[A-Za-z_][A-Za-z0-9_]*\s*=\s*[A-Za-z_][A-Za-z0-9_.]*$' .
```

When removing a root package export, search both import forms before deleting: a zero-match
scan for `from pkg import Symbol` misses `from parent import pkg` followed by
`pkg.Symbol` attribute access elsewhere. Grep for `import pkg` / `from parent import pkg`
alongside the named-symbol search, and confirm with the full test suite, not just an exact
reference scan.

### 3. Plan atomic commits

Plan before editing. Prefer one candidate or one mechanical migration per
commit, with a conventional imperative subject. Keep the default near 20
changed lines; exceed it only when a caller migration and deletion must stay
together to remain buildable and bisect-safe.

Use this order:

1. remove zero-caller aliases, dead exports, and `__all__` re-exports;
2. migrate callers from pure forwarding modules and `__init__.py` barrel exports directly to canonical modules;
3. delete the forwarding modules and re-export statements;
4. lock behavior with focused contract or parity tests;
5. migrate callers from behavior-bearing facades;
6. delete the old implementation after a zero-caller scan.

Do not mix unrelated cleanup into a migration commit. Any lint or type error
introduced within the active feature branch must be absorbed into the branch
commit that introduced it rather than creating a separate fixup commit.

### 4. Remove literal dead code

For zero-caller symbols and pure forwarding modules:

- delete the symbol or module rather than adding a replacement shim;
- remove stale exports, `__all__` declarations, and compatibility-only tests;
- migrate tests to canonical names and direct module imports when they still cover real behavior;
- rerun an exact import/reference scan;
- run focused tests, lint, and type checks before continuing.

### 5. Remove conceptual dead code

For an active facade, wrapper, defensive branch, or duplicate path:

1. identify the canonical behavior and its owning layer;
2. write or locate a contract test for normal, boundary, and failure behavior;
3. migrate one caller family at a time;
4. preserve output shape, scope, ordering, diagnostics, side effects, and error
   semantics unless the task explicitly changes them;
5. remove the old branch or facade once no callers remain;
6. rerun parity tests between old and new paths during the transition.

Use the `dead-code-knowledge` skill to classify defensive branches and
fallback code before removing them.

### 6. Delegate safely

Use subagents for bounded exploration or disjoint implementation slices. Give
each worker explicit file ownership, tell it not to revert other work, and do
not let workers edit overlapping files concurrently. Require each worker to
report changed files, commit hashes, reference scans, tests, and blockers.

The main agent owns classification, commit sequencing, integration, and final
verification. Review delegated diffs instead of assuming a zero-caller claim is
complete.

### 7. Verify the deletion

At minimum:

- exact zero-reference scans for removed names and modules;
- focused behavior tests;
- project lint and type checks;
- the default test suite for the repository.

Widen verification for runtime, daemon, MCP, storage, API, or serialization
changes. Restart long-lived processes and perform a live smoke test when the
removed code sits on a daemon or tool boundary. Check that generated or
installed copies are updated only through the repository's source-of-truth
workflow.

### 8. Capture the durable result

Record the classification decision, the evidence that made deletion safe, any
failure mode discovered, and the remaining next simplification. Report what
was deleted, what was intentionally retained, verification results, and any
uncertainty about dynamic or external consumers.

## Completion standard

Finish with a smaller canonical path, not a renamed compatibility layer. The
repository should have no stale exports, re-export shims (`__all__`/`__init__.py` forwarding),
dead tests, or comments claiming a removed compatibility contract. If a candidate remains,
state its evidence class and the concrete condition required to delete it later.
