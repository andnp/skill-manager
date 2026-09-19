---
name: architecture-knowledge
description: "Recognize when a codebase could be made structurally simpler: the standard for evaluating whether a boundary, engine, index, or reframing could replace whole families of code, and a leverage taxonomy for classifying reduction opportunities. Apply this whenever touching code and judging whether its design, not just its content, could be simpler — during ordinary refactoring, code review, or feature work, not only during a formal architecture audit."
---

# Architecture Knowledge

Use this skill whenever you are evaluating whether code could be structured more simply, whether or not anyone has asked for a formal audit. It gives the standard for recognizing reducibility and a taxonomy for classifying what you find.

## Core standard

Dream big. Dead-code removal is the lowest level of achievement, not the goal.

For any subsystem, ask whether a better representation or design could remove whole families of code:

- Can one capability-oriented boundary replace an oversized repository or service?
- Can a generic engine replace several nearly identical workflows?
- Can an index, cache, memoized representation, or incremental algorithm replace repeated full scans?
- Can a registry, schema, pipeline, or state machine replace branching and hand-written dispatch?
- Are multiple models or adapters translating between equivalent shapes?
- Can a canonical data structure make downstream code trivial?
- What would a 10x simpler design look like, and what evidence would make it safe to adopt?

Do not add abstraction for its own sake. Prefer changes that reduce conceptual paths, coupling, maintenance surface, or repeated work in addition to reducing LOC.

## Opportunity ledger: leverage taxonomy

Classify findings by leverage rather than by file type:

1. Literal dead code: unused settings, orphan modules, stale exports, unreachable aliases, and obsolete compatibility paths.
2. Redundancy: forwarding facades, duplicate helpers, repeated fallback paths, and equivalent model translations. When duplication is the primary complaint, or a candidate's implementations look different but may answer the same requirement or encode the same truth, use the `duplication-diagnostics` skill for the escalation ladder and diagnostic before ranking it here.
3. Boundary simplification: oversized repositories, unclear ownership, dynamic seams, and duplicated orchestration.
4. Problem reframing: algorithms, data structures, indexes, registries, pipelines, state machines, or incremental computation that could eliminate large regions of code.

Never call code dead solely because a simple text search found no caller. Check runtime entrypoints, dynamic access, external boundaries, fixtures, and contracts.
