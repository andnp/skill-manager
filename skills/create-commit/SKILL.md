---
name: create-commit
description: "Commit-driven development: plan commits with Andy before writing any code. TRIGGER — invoke at the START of any task that will produce code changes, before any implementation, whenever: asked to implement a feature, fix a bug, refactor code, or make any code changes. Read this skill FIRST — the commit plan must be agreed before touching code, never retrofitted after."
---

# Commit-Driven Development

Plan first. Implement one commit at a time. Never start coding before the plan is approved.

## Workflow

1. **Understand** — ask clarifying questions until the scope is unambiguous; don't plan against a fuzzy requirement
2. **Propose a commit sequence** — for plans with multiple commits, present a numbered list (see format below), including an estimated changed-line count for every commit; invite feedback and iterate until Andy approves. If the plan contains exactly one commit and the scope is unambiguous, do not ask for approval; execute it immediately.
3. **Implement commit N** — write only the code for that commit, nothing more
4. **Commit** — stage, write the message, create the commit
5. **Repeat** steps 3–4 for each remaining commit in the plan
6. **Request review** — "ready for your review" once all commits are done; stop and wait

Never implement a multi-commit plan before it is agreed. Never implement two commits' worth of work at once.

Default each commit to no more than about 20 changed lines, counting additions and
deletions. If a planned slice is larger, split it into independently valid slices
before implementation. Exceed the budget only when the changes cannot be separated
without breaking buildability or bisect safety, and explain that exception.

## Commit Plan Format

Present the plan as a numbered list before writing any code:

```
1. refactor(parser): extract token_stream helper
   Why: both the lexer and validator need it; avoids duplication

2. feat(parser): add support for nested expressions
   Why: required by the new grammar spec

3. test(parser): add tests for nested expression parsing
   Why: additive feat — separate commit per contract ownership rules
```

Each entry: conventional commit subject + one-line *why*. End with: "Does this split look right, or should anything be combined or broken apart?"

## Atomicity Rules

- A commit does exactly one thing — not two, not "one thing plus a drive-by fix"
- No "and" in the subject — if you need it, the commit needs splitting
- Small commits are good; lots of commits are good — err toward splitting, not batching
- Treat the 20-line budget as a planning constraint, not a post-hoc staging goal
- No minimum size — two lines is a fine commit
- Each commit must independently compile, lint, and pass tests (bisect-safe)
- Inseparable changes that break in isolation → combine rather than force a split
- If the working tree gets messy, replay the work step by step rather than staging hunks; clean history is worth it

## Commit Message Format

```
type(scope): subject  ← imperative mood, ≤72 chars; include scope when it adds signal
<blank line>
What changed and why. Never how — if how needs explaining, it belongs in a code comment.
```

Body is almost always required; omit only when the subject line is entirely self-evident.

| type | when |
|------|------|
| feat | new behavior |
| fix | bug fix |
| refactor | restructure, no behavior change |
| test | tests only |
| docs | docs only |
| chore | build / tooling / deps |
| perf | performance |

## Test Placement

- **Contract-breaking feat** — changes an existing call signature or behavioral guarantee → bundle test fixes into the feat commit; tests must never be broken between commits
- **Additive feat** — new function, module, or config field without touching existing contracts → separate follow-on test commit

## Anti-Patterns

- Never start implementing a multi-commit plan before the plan is approved
- Never write two commits' worth of changes then try to split after — revert and replay instead
- Never put "how" in the commit body (belongs in code comments)
- Fix linting/type errors introduced on an active feature branch by absorbing them into the commit that introduced them (via `git commit --amend`, `git rebase -i`, or `but absorb`), rather than stacking fixup commits
- Don't amend commits on shared integration branches (`main`/`master`) or branches you don't own
