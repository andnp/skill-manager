---
name: dead-code-knowledge
description: "Tell real dead code apart from code that looks dead but is load-bearing. Provides a 5-class evidence taxonomy (dead symbol, pure forwarding re-export, owned compatibility layer, conceptually dead behavior, live migration-or-resilience behavior) and an operating stance for judging deletion safety. Apply this any time you are deciding whether some code is safe to delete or is essential — not only during a formal dead-code audit: ordinary refactoring, a rename or move that makes another function look orphaned, reviewing a diff that deletes something, or reasoning about whether a fallback, shim, or defensive branch still earns its place."
---

# Dead Code Knowledge

Real dead code and load-bearing-looking-dead code are easy to confuse. Treat
literal reachability and conceptual obsolescence as separate problems, and
preserve behavior that protects external consumers, persisted data, runtime
availability, or an explicitly supported migration.

## Operating stance

- Names are clues, not evidence. A function named `fallback` may be essential;
  a function with an ordinary name may be a dead adapter. Verify against
  callers, entry points, and dynamic access rather than trusting the name.
- Treat an owned end application differently from a published library. An
  importable module is not automatically a public contract. If all callers
  are owned, migrating them and deleting the shim is safe; if any caller is
  external, it is not.
- Double down against re-export and forwarding patterns as an anti-pattern to
  be eliminated rather than tolerated. Python `__all__` lists, `__init__.py`
  re-exports (`from .module import Symbol`), TypeScript barrel files
  (`index.ts` re-exporting internal modules), and identity aliases add an
  indirection layer without adding behavior. Direct callers to import from
  canonical modules and delete the re-export wrapper outright.
- Do not add indefinite deprecation windows, release gates, or compatibility
  aliases without concrete evidence of an external consumer, persisted-data
  requirement, daemon cross-version requirement, or rollback requirement.
  Evidence of possible future need is not evidence of current need.
- A near-duplicate implementation that looks structurally different from the
  canonical path is not automatically a separate requirement — see this
  repository's duplication-diagnostics knowledge for distinguishing a real
  second requirement from a policy choice bolted onto one caller.

## Classify before deleting

Put every candidate in one evidence class:

1. **Dead symbol** — no source, test, configuration, script, entry-point, or
   documented runtime caller. Delete it.
2. **Pure forwarding code / re-export** — a re-export (`__all__`, `__init__.py`
   forwarding, barrel re-export), identity alias, empty subclass, or
   constructor that only forwards to the canonical implementation. Migrate
   owned callers to import directly from the canonical definition module,
   then delete the re-export.
3. **Owned compatibility layer** — callers still exist, but every caller is in
   the repository and the application owns the cutover. Migrate callers in a
   small slice, verify behavior, then delete the layer.
4. **Conceptually dead behavior** — code still runs but duplicates a canonical
   path, preserves an obsolete object shape, performs impossible-state
   recovery, or supports a retired architecture. Establish the replacement,
   migrate callers, prove parity, then remove the old path.
5. **Live migration or resilience behavior** — database migrations, replay
   handlers, cross-version daemon behavior, provider outage fallback, data
   repair, or user-input validation. Do not delete until the protected state
   or failure mode has a concrete replacement.

For fallback code specifically, identify what it protects before acting:

- user input or transient provider failure may be live behavior (class 5);
- persisted-data migration and replay support require explicit migration
  evidence (class 5);
- a fallback that only supports an obsolete internal caller is a deletion
  candidate after caller migration (class 3 or 4);
- a fallback that duplicates the canonical path should be collapsed, not kept
  as a second implementation forever (class 4).

For defensive code, distinguish valid boundary validation from
impossible-state handling. Broad `Any`, `getattr`, `hasattr`, catch-all
exceptions, and `None` wrappers should be narrowed only after proving the
typed construction path makes the defensive branch unreachable. Do not turn a
real provider, storage, or user-input failure into an assertion merely to
reduce lines.
