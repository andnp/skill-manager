---
name: duplication-diagnostics
description: "Recognize when code that looks different is actually duplicating the same truth or the same requirement, and when code that looks similar is not really duplication. Provides a 4-rung duplication ladder and a caller-vs-structural diagnostic for deciding whether two implementations can be unified. Apply this any time you are tempted to conclude two components 'solve different problems' because their APIs, data shapes, or lifecycles differ, or any time you are about to declare unification impossible."
---

# Duplication Diagnostics

An agent asked to find duplication will grep for similar-looking code, find
functions that share a lot of lines, and call it done. That is the lowest
possible bar and it is usually not where the value is. Two pieces of code with
near-identical text are easy to spot and often a minor win. Two pieces of code
that look *nothing alike* but answer the same requirement, encode the same
fact, or exist only because of how the system is carved up are the expensive,
high-value finds — and they are exactly what shape-based search misses.

Use this skill whenever you're comparing two implementations and deciding
whether they're duplicates, whether one can be removed in favor of the other,
or whether an apparent difference is real. Do not stop at rung 1 of the ladder
below.

## The duplication ladder

Classify what you're looking at onto one of these rungs. Rungs 3–4 usually
outrank rung 1 in leverage even at smaller line counts.

1. **Structural duplication** — copy-pasted or near-identical logic. Two
   functions with the same body, the same loop shape, the same sequence of
   calls. Easiest to find with text/AST similarity. Real, but usually cheap to
   fix and low architectural leverage.

2. **Duplicated truth** — the same fact, rule, or constraint is asserted in
   more than one place and must be kept in sync by convention rather than by
   construction. Two enums that must stay parallel, a validation rule
   reimplemented in the client and the server, a magic threshold copied into
   three call sites, a schema shape hand-derived in two modules. The code at
   each site can look completely different; what's duplicated is the fact, not
   the syntax.

3. **Redundant approaches to one requirement** — two (or more) implementations
   that exist to satisfy the *same caller need*, built independently, that
   look unrelated because they were solved from scratch each time. This is
   the subtlest and most valuable rung, and the one this diagnostic exists to
   catch — see below.

4. **Architectural duplication** — duplication that exists *because of* how
   the system is structured, not because anyone wrote similar code on
   purpose: parallel layers each re-deriving what another layer already
   computed, N adapters each translating between the same two shapes, a
   capability reimplemented per-service instead of owned once. Fixing this
   usually means a new module boundary, not a new helper function.

## The caller-vs-structural diagnostic

The failure mode this skill exists to prevent: an agent looks at two
implementations, sees they have different APIs, different data shapes, or
different lifecycles, and concludes they solve different problems — so
unification is declared impossible and the search moves on. That conclusion
is almost always reached by comparing the implementations' *current shapes*
instead of the *requirement* each one was actually built to satisfy.

Worked example, from a real case: a codebase had two subprocess-pipe readers.
One supported early cancellation and worked with a bounded capture window;
the other ran for the full lifetime of the process and had no cancellation.
An agent asked to unify them concluded they were fundamentally different —
"bounded and cancellable" vs. "unbounded and full-lifetime" — and kept them
separate, sharing only some thread-lifecycle boilerplate. That was wrong. The
actual requirement behind both was identical: *drain a long-lived process's
stderr on a background thread without blocking it, and signal when draining
is done.* Cancellation wasn't evidence of a different requirement — it was a
policy one specific caller layered on top by choosing to call `stop()`. If
that caller simply never calls `stop()`, the "bounded" reader behaves exactly
like the "full-lifetime" one. Once that was seen, both were rebuilt on one
shared pipe-drain primitive, with cancellation as an optional capability
instead of a structural fork. The unification that had been called
impossible took about five small commits once the actual requirement was
named.

Before writing "not duplication, these solve different problems" about any
candidate, answer in writing:

- What is the requirement each *caller* actually has — not what API each
  current implementation happens to expose?
- For every point where the implementations differ, is that difference a
  property the component must have, or a policy choice exercised by one
  specific caller?
- If you removed that caller's use of the differentiating behavior (don't
  call `stop()`, don't set the flag, don't take the extra branch), does the
  component degrade into exactly the other implementation's use case?

If the answer to the last question is yes, the "difference" was never
structural — it's one requirement with an optional capability bolted on by
one caller, and it belongs to rung 3.
