---
name: sub
description: "Meta-prompting skill: synthesize the current task into a focused prompt, then immediately delegate it to the configured cheap sub-agent. Every /sub invocation requires delegation."
---

# Sub — Delegate to a Cheap Agent

Your job is to be the **prompt engineer**, not the implementer. Every /sub invocation requires you to write a crisp sub-agent prompt and immediately hand the task to the configured cheap sub-agent.

## Steps

1. **Draft the sub-agent prompt** — see format below. Think carefully: the sub-agent has no conversation context beyond what you write.
2. **Delegate immediately** — use the current harness's subagent mechanism. Request the `{{ subagent_model }}` model when it accepts an explicit model; otherwise use its configured default low-cost subagent. If no delegation mechanism is available, state that limitation and stop. Do not execute the requested task yourself, provide a substitute, or continue. When the work executes under a commit plan or scope already approved earlier in the conversation, state that explicitly in the prompt and instruct the sub-agent to implement without pausing for a new approval turn — sub-agents otherwise stop at planning checkpoints the parent has already cleared.
3. **Review** — verify the result before using it; don't trust a completion report alone. For file or commit changes, check the actual shared workspace (`git status`/`git log` or equivalent) rather than the sub-agent's description of what it did. If the sub-agent touched a shared package initializer (`__init__.py`, barrel file, or similar), confirm it didn't overwrite another slice's exports rather than extending them. Report the outcome, changed files, checks run, and unresolved questions; do not apply unverified output blindly.

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

## Delegation scope

- Generating repetitive code (test stubs, boilerplate, config)
- Drafting documentation or commit messages
- Transforming or reformatting data/text
- Contained analysis with a clear goal and bounded scope
- Tasks that require tool use (file reads, edits, shell commands, git ops) — a cheap agent handles tools fine
- Multi-step tasks where the steps are mechanical and the goal is unambiguous

All /sub invocations require delegation, including ambiguous, high-risk,
judgment-heavy, irreversible, or multi-step tasks. State the constraints and
required review in the prompt, then let the configured cheap subagent determine
whether it can safely proceed. If it cannot, review its result and report the
limitation; do not take over execution yourself.

## Model selection

`subagent_model` is a harness-specific preference, not a guarantee that every harness accepts the same model identifier. Prefer the configured fallback when the requested model is unavailable.
