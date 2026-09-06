---
name: improve-api
description: "Improve an owned API from evidence in real consumers, prioritizing developer ergonomics, minimal public surface, and a clean canonical end state without compatibility scaffolding."
---

# Improve API

Use this skill for API redesigns, boundary improvements, and consumer-driven
refactors. Do not use it for routine bug fixes, documentation-only changes, or
an additive helper whose existing boundary is already adequate.

## Operating principles

- Inspect before designing. Read repository instructions, package metadata,
  the current API, tests, and real consumers.
- Use only concrete pain in real consumers as evidence. A consumer's existence
  is not proof that its full shape belongs in the shared API.
- Choose one focused boundary problem. If the evidence supports only a local,
  bespoke adapter, keep that behavior in the consumer instead of generalizing it.
- Optimize for developer ergonomics: readable call sites, discoverable names,
  low ceremony, useful validation errors, and clear ownership of behavior.
- Treat the public API as a budget. Prefer the fewest methods and attributes
  that preserve the required expressivity through composition.
- Do not add speculative extension points, configuration knobs, aliases, or
  compatibility wrappers.
- Unless the user explicitly requests compatibility, finish with one canonical
  implementation and remove the superseded path, callers, tests, exports, and
  configuration owned by the repository.

## Workflow

### 1. Establish the evidence

Read the repository's local instructions and search memory when available.
Inspect the current boundary, its tests, and its consumers. Trace the behavior
far enough to distinguish:

- repeated policy that belongs in the shared API;
- leakage of storage, schema, lifecycle, or implementation details;
- awkward ceremony or invalid states forced on callers;
- genuinely unique consumer behavior that should remain a small adapter.

Record the single problem selected and the evidence for it. Do not turn every
consumer variation into a requirement.

### 2. Specify the end-state contract

Write the intended call syntax before implementation. Define:

- the smallest public surface;
- the observable result and ownership of each behavior;
- normal, boundary, and invalid-input semantics;
- validation and error behavior;
- what the API deliberately does not support;
- which old paths must disappear when the change is complete.

Prefer a small composable interface over a broad object with convenience
methods. A consumer adapter is appropriate when it performs bespoke work that
is not supported by multiple real consumers.

### 3. Lock the contract with TDD

Add a deterministic test using the exact proposed syntax and expected result.
Mark it `pytest.mark.xfail(..., strict=True)` until the implementation exists.
Test externally visible behavior, not private structure. Include the most
important invalid or boundary case when it defines the contract. Use a real or
disposable fixture when the boundary depends on storage or external state;
do not let an optional checked-in artifact make the test pass without testing
the new contract.

### 4. Implement the canonical path

Implement only the selected contract. Keep policy in the owning layer and keep
consumer-specific behavior at the consumer boundary. Remove the superseded
implementation in the same change when it is repository-owned and no explicit
compatibility requirement protects it.

During review, check both behavior and shape:

- Does the API solve the demonstrated pain with fewer concepts exposed?
- Are names and call sites obvious without reading implementation details?
- Did implementation convenience leak extra methods or attributes?
- Did a real consumer need a local adapter that was incorrectly generalized?
- Is any old or parallel path still active unintentionally?

### 5. Verify and close the loop

Run the focused contract tests first, then the repository's relevant lint,
type, integration, and broader test checks. Chain verification gates with
`&&` before irreversible actions such as committing so a failed check blocks
the action.

Report the final API shape, changed ownership boundaries, validation results,
pre-existing failures, deliberately retained consumer adapters, and any
deferred work. Record durable design decisions and reusable failure modes, not
routine exploration.

## Completion standard

The task is complete when the real consumer pain is addressed by the smallest
expressive public API, the contract is executable, repository-owned legacy paths
are gone unless explicitly protected, and bespoke consumer behavior remains
local rather than bloating the shared boundary.
