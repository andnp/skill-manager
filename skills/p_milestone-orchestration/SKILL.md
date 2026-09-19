---
name: p_milestone-orchestration
description: "Break a large migration or design doc into milestones and deliver each via a subagent that proposes a fine-grained commit plan before implementing. Use when asked to implement or migrate toward a large design doc/plan using subagents, or to 'work autonomously' through a big body of work with commit-plan approval checkpoints. Invoke only when explicitly requested by name; do not self-trigger."
invocation: manual
---

# Milestone Orchestration

For work too large for one commit plan (a design doc, a multi-phase migration):
decompose into milestones, then deliver each milestone through a cheap
subagent that plans before it codes. You are the orchestrator — you drive the
subagent through planning, approval, and implementation yourself; the user
only ever sees and drives milestones.

Every milestone is delegated. Do not implement a milestone yourself — spawn
the configured cheap subagent (`{{ subagent_model }}` on this harness; fall
back to its default low-cost subagent if that model is unavailable) for both
the commit plan and the implementation.

## Workflow

1. **Agree on milestones with the user first.** Propose a milestone list —
   coarser than a commit, ordered by dependency — sized to roughly 10 commits
   of work each. Get the user's explicit agreement on this list before
   starting any implementation. This is the only level the user plans at;
   nothing finer-grained goes back to them.
2. **Sanity-check the milestone list** before starting — for a risky or
   architecturally significant migration, get an outside opinion (see
   `delegate-code-review`) on the sequencing and scope, not just the code.
3. **For each milestone, sequentially** (never parallel — they share one
   worktree/branch):
   - Spawn the cheap subagent with the milestone's context. Instruct it to
     inspect repo conventions and return ONLY a fine-grained commit plan (see
     `create-commit`: ~20-line budget, conventional commits, why-focused
     bodies) — no code yet.
   - Review the plan yourself and give the subagent feedback or approval;
     iterate until it's right. Do not surface the commit plan to the user —
     they only care about the milestone, not its internal commit breakdown.
   - Once you approve it, tell the **same** subagent to implement, committing
     directly to the current branch in the current worktree — no new
     branch/worktree per milestone. It runs the repo's own lint/type/test
     checks after each commit so every commit is independently bisect-safe.
   - Once the milestone's commits have landed, spin up a **fresh, separate**
     subagent (not the one that implemented it) to review the resulting code.
     Feed it back into the same implementing subagent for fixes if it finds
     problems, then re-review before moving on.
   - Only start the next milestone once this one is implemented and reviewed.
4. Record durable findings (repo-convention discoveries, deferred scope,
   caller inventories) as you go so a later milestone doesn't re-derive them.
5. Report progress to the user at the milestone level only: which milestone
   just landed, what the fresh review found, and what's next.

## Why sequential, not parallel

Milestones commonly depend on each other's output (a table before the
repository that reads it, a domain type before the algorithm using it), and
all agents share one worktree — running them concurrently risks one agent's
commit landing mid-way through another's edits. Parallelize only independent,
non-overlapping milestones, and only with separate worktrees.

## Model selection

`subagent_model` is a harness-specific preference, not a guarantee that every
harness accepts the same model identifier. Prefer the configured fallback
when the requested model is unavailable. Use this same model for both the
planning subagent and the fresh review subagent.
