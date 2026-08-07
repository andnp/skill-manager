---
name: write-good-tests
description: Use whenever you write, modify, review, or plan software tests of any kind, including unit, component, integration, contract, acceptance, end-to-end, performance, security, and exploratory tests. Apply the testing principles in this skill to choose test boundaries, generate meaningful cases, avoid brittle implementation-coupled tests, and verify the resulting suite.
---

# Write Good Tests

Design tests as a fast feedback and learning system, not as a checklist of lines to execute. This skill applies across languages and frameworks and helps an agent produce tests that protect important behavior, tolerate valid refactoring, expose useful failures, and fit the project’s delivery workflow.

## Core philosophy

Follow these principles in every test task:

- **Test behavior, not implementation.** Assert outcomes, contracts, and externally meaningful effects. Do not inspect private state or incidental call order just to increase coverage.
- **Optimize for confidence over test count.** A test is valuable when it catches meaningful regressions, resists harmless refactoring, runs quickly enough to use, and remains understandable.
- **Prefer the smallest test that provides the needed confidence.** Use narrow tests for local logic and larger tests only when the risk crosses a real component, process, deployment, or user boundary.
- **Keep tests deterministic and hermetic.** Control time, randomness, environment, network, filesystem, process state, and test data. Isolate tests from one another.
- **Use real dependencies when they are fast and reliable.** Prefer a real implementation, then a focused fake, before a mock. Mock mainly at boundaries with externally visible side effects.
- **Test failure behavior deliberately.** Include invalid input, unavailable dependencies, timeouts, retries, partial failures, authorization failures, and recovery paths when the product must handle them.
- **Treat tests as executable documentation.** Use clear names, local setup, focused assertions, and failure messages that explain what behavior was expected.
- **Make quality a team-owned, continuous activity.** Developers and testers share responsibility; run tests continuously and repair broken or flaky tests promptly.
- **Use coverage and metrics as signals, not targets.** Coverage can reveal gaps, but it cannot prove that assertions are meaningful.
- **Use production feedback as another test oracle.** Monitoring, canaries, probes, and safe rollback complement pre-release tests.

When principles conflict, prioritize in this order: user-visible or contractual behavior, risk reduction, determinism, useful feedback, maintainability, then convenience or raw coverage.

Evaluate each proposed test against four quality pillars: protection against regressions, resistance to harmless refactoring, fast feedback, and maintainability. A test that is strong on only one pillar may still be a poor trade.

## Workflow for writing tests

### 0. Classify the change before writing code

- **Bug fix:** reproduce the bug with a focused failing regression test, then fix it.
- **New behavior:** define the observable contract and cases before implementation; use red–green–refactor when practical.
- **Refactor:** preserve existing behavior and change tests only when the contract changes.

For cross-component behavior, consider starting with a thin acceptance test or walking skeleton, then drive the internals with focused tests. Record the risk, boundary, and intended cases before implementation when the change is non-trivial.

### 1. Understand the behavior and local conventions

Before editing, inspect the implementation, its public interfaces, nearby tests, fixtures, test commands, and project conventions. Reuse existing helpers and data builders when they make scenarios clearer. Do not invent a new framework, test style, or directory layout when the project already has one.

State the behavior under test in plain language. Identify the client goal, observable result, side effects, invariants, and failure modes. If requirements are ambiguous, test the strongest behavior supported by current evidence and call out the assumption.

### 2. Choose the test boundary deliberately

Use the narrowest suitable level, but do not force a unit test where the risk is inherently broader.

- **Unit:** one focused behavior or small unit of domain logic; fast, isolated, and precise.
- **Component:** one deployable or cohesive component through its supported interface.
- **Integration:** real interaction between selected components or with a real database, queue, filesystem, or service substitute.
- **Contract:** compatibility between independently evolving producers and consumers.
- **End-to-end / acceptance:** a critical user journey through the deployed system; keep the set small and high-value.
- **Performance / load:** explicit response-time, throughput, capacity, or resource risks under controlled conditions.
- **Security / reliability:** authorization, data exposure, abuse cases, degradation, recovery, and fault-injection scenarios.
- **Exploratory:** time-boxed investigation guided by a charter; use it to discover unknown risks and turn important discoveries into repeatable automated checks.

Use more than one level when each level answers a different question. Do not duplicate the same assertion across every layer without a reason.

Contract tests answer “can these independently deployed systems communicate?”; integration tests answer “do these components work together in this environment?” Use consumer/provider contracts when compatibility matters more than shared deployment.

### 3. Build a behavior and risk matrix

For each behavior, consider:

1. Happy path and representative normal inputs.
2. Empty, missing, zero, one, many, maximum, and unusually large values.
3. Invalid input, malformed data, unsupported combinations, and boundary transitions.
4. State changes, idempotency, ordering, concurrency, retries, and repeated calls.
5. Dependency errors, timeouts, unavailable services, partial success, and recovery.
6. Authentication, authorization, tenancy, privacy, and sensitive-data handling.
7. Accessibility, localization, compatibility, observability, and performance where relevant.

Select cases by risk and behavior, not by mechanically enumerating every branch. Parameterize only when the cases remain easy to understand and failures identify the specific scenario.

When a rule is an invariant over a broad input space, consider property-based or fuzz testing with controlled seeds and shrinkable failures. Use examples alongside generated cases for readability.

### 4. Implement readable, robust tests

Use a clear Arrange–Act–Assert (or Given–When–Then) shape. Keep one conceptual behavior per test and one main act where practical. Prefer explicit local values over distant shared fixtures; use small builders or factories only to hide irrelevant defaults.

Assertions should verify observable outcomes and include useful expected-versus-actual diagnostics. Avoid assertions that merely prove a method was called unless the call itself is the externally meaningful behavior (for example, publishing an event to another system).

Avoid sleeps. Use controllable clocks, deterministic schedulers, polling with bounded timeouts, event notifications, or other synchronization that waits for a condition rather than an arbitrary duration.

When using doubles:

- Prefer a real dependency if it is cheap and deterministic.
- Prefer a fake with meaningful behavior when a real dependency is impractical.
- Stub only the values needed by the scenario.
- Mock externally visible side effects or interactions whose count/order is itself a requirement.
- Avoid overspecifying incidental arguments, helper calls, or internal collaboration graphs.

### 5. Verify and maintain the suite

Run the narrowest relevant test command first, then the broader project checks required by local conventions. Investigate failures rather than weakening assertions or adding retries by default. A flaky test is a defect in the testing system until its cause is understood.

For larger tests, provide clear failure output, trace or diagnostic artifacts, a named owner, and a reason the test cannot be smaller. Keep the main developer workflow fast; isolate expensive suites to appropriate build, release, or scheduled stages.

## Test-case output requirements

When asked to write tests, produce:

- Behavior-named tests covering relevant normal, boundary, invalid, and failure cases.
- The smallest appropriate mix of test levels, with a reason for each larger test.
- Deterministic setup, isolated external state, and assertions tied to a contract.
- No private-state inspection, low-value duplication, or incidental call-sequence checks.
- A concise note of assumptions, residual risks, and commands run.

When reviewing existing tests, classify findings as missing risk coverage, false confidence, brittleness, nondeterminism/flakiness, slow feedback, unclear failure diagnosis, or unnecessary duplication. Fix the test design, not merely the symptom.

## Anti-patterns to reject

- Test suites shaped like an “ice-cream cone”: many end-to-end tests and few fast, focused tests.
- Tests that pass only because they mock every dependency.
- Tests coupled to private fields, concrete class structure, or exact internal call order.
- Shared mutable fixtures, order-dependent tests, real clock sleeps, random data without controlled seeds, and tests that depend on a developer machine.
- A universal coverage percentage used as a substitute for risk analysis.
- Large tests with no owner, no diagnostics, and no explanation of the risk they cover.
- Broad “validate everything” helpers that hide which behavior a test actually checks.
- Weakening a test because the implementation is difficult to test; treat that difficulty as design feedback.

## Final checklist

Before finishing, ask:

- What user-visible or contractual behavior does each test protect?
- Would the test still pass after a correct refactor?
- Is it isolated, deterministic, fast enough, and clear when it fails?
- Did the cases cover meaningful boundaries, failures, and residual risks?
- Is the dependency strategy and test boundary justified?
- Did I run the relevant checks and report the result honestly?
