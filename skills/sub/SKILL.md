---
name: sub
description: "Meta-prompting skill: synthesize the current task into a focused prompt, then delegate it to a cheap sub-agent. Use when the task is well-scoped and can be handed off — e.g. generating boilerplate, running a contained analysis, drafting a repetitive artifact, or any task where a cheap agent's speed and low cost fit the work."
---

# Sub — Delegate to a Cheap Agent

Your job is to be the **prompt engineer**, not the implementer. Decide whether the task is bounded enough to delegate, write a crisp sub-agent prompt, then hand it off when the current harness supports delegation.

## Steps

1. **Assess the task** — delegate only bounded, reversible work with a clear success condition. Handle ambiguous, high-risk, or judgment-heavy work yourself.
2. **Draft the sub-agent prompt** — see format below. Think carefully: the sub-agent has no conversation context beyond what you write.
3. **Delegate** — use the current harness's subagent mechanism. Request the `{{ subagent_model }}` model when it accepts an explicit model; otherwise use its default low-cost subagent. If no delegation mechanism is available, handle the task yourself and say so.
4. **Review** — verify the result before using it. Report the outcome, changed files, checks run, and unresolved questions; do not apply unverified output blindly.

## Sub-agent prompt format

Write the prompt as if briefing a capable colleague who just walked in with zero context:

```
## Task
<one-sentence goal>

## Context
<what the sub-agent needs to know: relevant file paths, symbols, constraints, prior decisions>
<include verbatim snippets or file contents if small enough — the sub-agent cannot read the conversation>

## Output
<exact format expected: code block, list, JSON schema, prose, etc.>
<hard constraints: line limits, style rules, no new dependencies, etc.>
```

## Good candidates

- Generating repetitive code (test stubs, boilerplate, config)
- Drafting documentation or commit messages
- Transforming or reformatting data/text
- Contained analysis with a clear goal and bounded scope
- Tasks that require tool use (file reads, edits, shell commands, git ops) — a cheap agent handles tools fine
- Multi-step tasks where the steps are mechanical and the goal is unambiguous

## Bad candidates

- Tasks so ambiguous that even you couldn't write a clear prompt for them
- Judgment calls that require weighing the full conversation history to decide correctly
- Security-sensitive, irreversible, or high-impact changes
- Tasks explicitly requiring a stronger model than the configured subagent

Delegate when the task is well-scoped and the expected review cost is lower than doing the work directly. Do not delegate merely because a task has multiple steps.

## Model selection

`subagent_model` is a harness-specific preference, not a guarantee that every harness accepts the same model identifier. Prefer the configured fallback when the requested model is unavailable.
