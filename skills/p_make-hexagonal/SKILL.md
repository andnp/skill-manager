---
name: p_make-hexagonal
description: "Find exactly one small, behavior-preserving boundary improvement toward hexagonal architecture, keep production and test changes within a 100-line budget, and propose the change before implementing it. Invoke only when explicitly requested by name; do not self-trigger."
invocation: manual
---

# Make Hexagonal

Move a codebase incrementally toward hexagonal architecture through one concrete, reviewable improvement. This skill is language-, framework-, and repository-layout agnostic; use it primarily for explicit human requests such as “make this more hexagonal” or “find one place to introduce a port.”

## Hexagonal architecture in practice

Use hexagonal architecture to make application decisions independent from infrastructure details:

- **Ports** describe the capabilities the application needs or exposes.
- **Adapters** connect those ports to concrete technologies, processes, frameworks, or environments.
- Dependencies point inward toward application or domain logic.
- The composition root chooses concrete adapters and wires the application together.
- The goal is a useful boundary, not an interface around every class or a new dependency-injection framework.

Prefer an incremental seam over architectural purity. Preserve behavior unless changing behavior is explicitly part of the request.

## Workflow

### 1. Establish the boundary

Before editing:

- Identify the repository or subrepo that owns the requested change.
- Read applicable agent instructions, project configuration, and the relevant test and validation commands.
- Trace one concrete flow from an entry point through application logic to its infrastructure interaction.
- Locate the composition root and any existing ports, protocols, interfaces, factories, or adapters.
- Use repository architecture/search tools when available; otherwise use focused symbol, caller, and file searches.
- Inspect enough context to understand one seam. Do not perform a repository-wide architecture audit.

Look for concrete coupling, such as application logic directly constructing or calling process, storage, network, clock, framework, or external-service details. Treat search results as leads and verify the flow in current code.

### 2. Select exactly one opportunity

You may discover several candidates, but select exactly one. Rank candidates by:

1. Clear improvement in dependency direction or boundary ownership.
2. Localized scope with unchanged behavior.
3. A concrete validation path, preferably an existing or focused behavioral test.
4. Reuse of an existing abstraction or a narrow seam with an immediate benefit.
5. A useful foundation for future work without requiring that future work now.

Prefer opportunities such as passing an existing adapter from the composition root, moving infrastructure construction outward, routing restored or discovered objects through an existing boundary, or replacing one direct infrastructure call with a narrow port.

Reject opportunities that require broad package reorganization, a generic dependency-injection framework, speculative interfaces, mass renaming, unrelated cleanup, or simultaneous behavior changes.

### 3. Enforce the hard budget

The complete implementation must change at most 100 lines, counting additions and deletions in production code and tests. Do not meet the budget by omitting necessary tests, hiding formatting churn, or weakening correctness. If the best candidate cannot fit, reject it and choose a smaller one.

Estimate the diff before implementation and recount the final diff afterward. Stop and ask for direction if the selected change would exceed the budget.

### 4. Propose before editing

Present one proposal containing:

- the selected boundary and current coupling;
- why it is the strongest single opportunity;
- the expected dependency-direction improvement;
- likely files or components affected;
- estimated additions plus deletions;
- the focused validation plan; and
- explicit non-goals and the stopping condition.

Pause for human approval before implementation unless the user explicitly asked for autonomous execution. If the user asks for a different opportunity, replace the proposal rather than accumulating candidates.

### 5. Implement the approved slice

- Make the smallest coherent, behavior-preserving change.
- Keep infrastructure-specific details at the edge and application policy inside.
- Prefer existing ports, protocols, factories, and composition roots.
- Add or update focused behavioral coverage when the seam needs protection.
- Avoid unrelated cleanup, speculative compatibility paths, and broad renames.
- Recheck the line budget after each meaningful edit; stop when the stated stopping condition is met.

### 6. Validate and hand off

Run the narrowest relevant checks first, then widen them according to the affected boundary: project linting, type checks, focused tests, and integration or smoke checks when runtime wiring changed. Inspect the final diff and verify the additions-plus-deletions count is at most 100.

Report:

- the boundary improved and the behavior preserved;
- the files changed and final line count;
- validation performed and any uncertainty; and
- deliberate follow-up work that remains out of scope.

Do not implement a second opportunity in the same run. A successful result is one small step toward clearer dependency direction, not a complete architecture migration.
