---
name: p_deduplicate-codebase
description: "Scan an owned codebase for duplication, rank up to 10 sources by severity and complexity, and recommend a restructure, new abstraction, or architectural pivot that removes the duplicated truth rather than the duplicated text. Delivers through the repository's language, testing, and commit skills rather than freelancing the implementation. Use when asked to deduplicate, consolidate, unify implementations, or reduce redundancy in owned code. Invoke only when explicitly requested by name; do not self-trigger."
invocation: manual
---

# Deduplicate Codebase

Use this skill when the user wants duplication found and removed. The deliverable
is not a list of similar-looking functions. It is a small number of high-leverage
restructures that remove a duplicated *truth*, each delivered as reviewed,
tested, committed work.

Apply the `duplication-diagnostics` skill throughout this workflow — it holds
the duplication ladder (structural / duplicated-truth / redundant-approaches /
architectural) and the caller-vs-structural diagnostic used to classify and
rank candidates below. This skill does not restate that material; read
`duplication-diagnostics` before step 2.

## 1. Scan

Read repository-local instructions, architecture documentation, and the
nearest tests before touching code. Use `repowise` or an equivalent
symbol/caller tool for architecture and cross-file questions when available;
fall back to `rg` and direct reads for configuration, scripts, and gaps in
indexed context.

Look across the whole owned codebase, not just one module — architectural and
requirement-level duplication is often invisible from inside either duplicate
site and only shows up when comparing distant parts of the system.

For duplicated-truth and higher candidates specifically, search by *concept*
rather than by *text*: grep for the fact or rule by name/value across the
repo (a constant, a status code, a business rule), and ask what each caller
actually needs before comparing how it's currently gotten.

## 2. Build a ranked duplication ledger

Produce **up to 10** candidates, ranked by severity × complexity of removal —
not by raw line count matched. Classify each with the `duplication-diagnostics`
ladder, and for anything you're tempted to dismiss as "different problems",
apply its caller-vs-structural diagnostic before excluding it. For each
candidate:

| Candidate | Ladder rung | Sites (files/symbols) | Duplicated truth or requirement | Diagnostic result (if rung 3) | Severity | Removal complexity | Recommended fix |
| --- | --- | --- | --- | --- | --- | --- | --- |

- **Severity** should reflect real cost: how often the sync-by-convention
  breaks in practice, how many places a future change must touch, whether it
  has already caused a bug from the copies drifting.
- **Removal complexity** should reflect real risk: number of callers, whether
  behavior contracts differ today for reasons that matter, test coverage.
- A rung-3/4 finding with 3 call sites and no test coverage may rank above a
  rung-1 finding with 20 copy-pasted lines and full coverage — leverage beats
  volume.

Do not pad the list to 10 with marginal rung-1 matches if genuine rung 2–4
findings exist; a shorter, higher-leverage list is a better deliverable than a
padded one.

## 3. Recommend the restructure

For each candidate you intend to act on, name the concrete design move, not
just "reduce duplication":

- a new shared class, function, or module that becomes the one place the
  duplicated truth lives;
- a new or widened API on an existing type that removes the need for
  independent reimplementation;
- a data structure, registry, schema, or single source of record that makes
  the fact structurally impossible to duplicate (encode it once; derive
  everything else);
- an architectural pivot — a moved boundary, a merged layer, a shared adapter —
  when the duplication is rung 4 and a new helper function would just be
  another site to keep in sync.

State what gets deleted, not just what gets added. A restructure that adds a
shared abstraction but leaves both old call sites in place has not removed the
duplication — it added a third thing to keep in sync. Every accepted candidate
ends with exactly one canonical path and the superseded implementations
removed, per this repository's canonical-replacement rules.

## 4. Deliver through the right skills — do not freelance the implementation

This skill is diagnostic and design-first, not a substitute for the
repository's language, testing, or commit workflow skills. Before touching
code:

- Identify and read the applicable language-specific skill(s) for the
  languages involved (for example a Python style skill, a TypeScript
  convention skill) and follow their conventions for the restructure.
- Identify and read the applicable testing skill and use it to decide test
  boundaries for the new canonical path and for proving behavior parity with
  what's being removed.
- Identify and read the applicable commit-pattern / version-control skill
  (commit planning, atomic commit shape, GitButler vs. plain git) and plan the
  commit sequence with it before writing code.

Do not invent ad hoc testing or commit conventions when a repository skill
already covers them. If no matching skill exists for a given language or
concern, fall back to the general engineering and testing guidance already in
force for this session, and say so explicitly rather than silently improvising.

## 5. Validate

For each delivered restructure:

- prove behavior parity between the removed implementations and the new
  canonical path (contract/parity tests before deleting the old code, not
  after);
- run a zero-caller scan on anything deleted;
- run the repository's lint, type, and test checks at the narrowest scope
  first, then widen when the change crosses module boundaries or affects
  runtime/integration behavior;
- report, per candidate: ladder rung, what was unified, what was deleted, net
  LOC, and any duplication you found but deliberately deferred, with the
  reason (e.g. genuinely different requirements confirmed via the diagnostic,
  not just "looked different").

## Completion standard

Finish with fewer independent places encoding the same fact or answering the
same requirement — not with a shared helper sitting alongside untouched
duplicates, and not with a list of copy-pasted blocks that stopped at rung 1.
If a candidate was left unresolved, its ledger entry must state which rung it
was on and why the diagnostic in `duplication-diagnostics` did not clear it
for unification.
