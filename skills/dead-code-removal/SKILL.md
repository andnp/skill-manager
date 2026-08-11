---
name: dead-code-removal
description: "Audit and remove literal dead code, obsolete compatibility shims, legacy-shaped facades, redundant defensive branches, stale exports, and duplicated fallback paths. Use when slimming an owned application or library, retiring a migration layer, deleting unused symbols, simplifying an architecture, or separating necessary resilience from conceptual dead code."
---

# Dead Code Removal

Use this skill to make a repository smaller by evidence, not by deleting every
symbol whose name contains `legacy`, `compat`, `fallback`, or `deprecated`.
Treat literal reachability and conceptual obsolescence as separate problems.
Preserve behavior that protects external consumers, persisted data, runtime
availability, or an explicitly supported migration.

## Operating stance

- Inspect repository instructions, package metadata, entry points, and current
  worktree state before changing anything.
- Search project memory first when memory tooling is available; read relevant
  records fully before relying on them.
- Treat an owned end application differently from a published library. An
  importable module is not automatically a public contract. If all callers are
  owned, migrate them and delete the shim outright.
- Do not add indefinite deprecation windows, release gates, or compatibility
  aliases without concrete evidence of an external consumer, persisted-data
  requirement, daemon cross-version requirement, or rollback requirement.
- Preserve unrelated user changes. Never reset a dirty worktree to make the
  audit easier.

## Classify before deleting

Put every candidate in one evidence class:

1. **Dead symbol** — no source, test, configuration, script, entry-point, or
   documented runtime caller. Delete it.
2. **Pure forwarding code** — a re-export, identity alias, empty subclass, or
   constructor that only forwards to the canonical implementation. Migrate
   owned callers, then delete it.
3. **Owned compatibility layer** — callers still exist, but every caller is in
   the repository and the application owns the cutover. Migrate callers in a
   small slice, verify behavior, then delete the layer.
4. **Conceptually dead behavior** — code still runs but duplicates a canonical
   path, preserves an obsolete object shape, performs impossible-state
   recovery, or supports a retired architecture. Establish the replacement,
   migrate callers, prove parity, then remove the old path.
5. **Live migration or resilience behavior** — database migrations, replay
   handlers, cross-version daemon behavior, provider outage fallback, data
   repair, or user-input validation. Do not delete until the protected state or
   failure mode has a concrete replacement.

Names are clues, not evidence. A function named `fallback` may be essential;
a function with an ordinary name may be a dead adapter.

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

Use `rg`/`rg --files` first. Use codegraph or an equivalent symbol/caller tool
when available for architecture questions, then verify findings against files.
Search names, import paths, constructor calls, string registrations, config
keys, and serialized field names. A zero textual match is not enough when
reflection or plugin discovery exists.

Useful starting searches include:

```bash
rg -n '(compat|compatib|legacy|deprecated|shim|facade|adapter|wrapper|alias|fallback)' src tests
rg -n '__all__|entry_points|import_module|getattr\(|hasattr\(|register|plugin' .
rg -n 'from .* import \*|^\s*[A-Za-z_][A-Za-z0-9_]*\s*=\s*[A-Za-z_][A-Za-z0-9_.]*$' src
```

### 3. Plan atomic commits

Plan before editing. Prefer one candidate or one mechanical migration per
commit, with a conventional imperative subject. Keep the default near 20
changed lines; exceed it only when a caller migration and deletion must stay
together to remain buildable and bisect-safe.

Use this order:

1. remove zero-caller aliases and dead exports;
2. migrate callers from pure forwarding modules;
3. delete the forwarding modules;
4. lock behavior with focused contract or parity tests;
5. migrate callers from behavior-bearing facades;
6. delete the old implementation after a zero-caller scan.

Do not mix unrelated cleanup into a migration commit. Do not create a fixup
commit for lint or type errors introduced by your own change; correct the
originating commit.

### 4. Remove literal dead code

For zero-caller symbols and pure forwarding modules:

- delete the symbol or module rather than adding a replacement shim;
- remove stale exports and compatibility-only tests;
- migrate tests to canonical names when they still cover real behavior;
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

For defensive code, distinguish valid boundary validation from impossible-state
handling. Replace broad `Any`, `getattr`, `hasattr`, catch-all exceptions, and
`None` wrappers only after proving the typed construction path makes them
unreachable. Do not turn a real provider, storage, or user-input failure into
an assertion merely to reduce lines.

For fallback code, identify what it protects:

- user input or transient provider failure may be live behavior;
- persisted-data migration and replay support require explicit migration
  evidence;
- a fallback that only supports an obsolete internal caller is a deletion
  candidate after caller migration;
- a fallback that duplicates the canonical path should be collapsed, not kept
  as a second implementation forever.

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
repository should have no stale exports, dead tests, or comments claiming a
removed compatibility contract. If a candidate remains, state its evidence
class and the concrete condition required to delete it later.
