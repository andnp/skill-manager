---
name: sub
description: "Meta-prompting skill: synthesize the current task into a focused prompt, then delegate it to a cheap sub-agent. Use when the task is well-scoped and can be handed off — e.g. generating boilerplate, running a contained analysis, drafting a repetitive artifact, or any task where a cheap agent's speed and low cost fit the work."
---

# Sub — Delegate to a Cheap Agent

Your job is to be the **prompt engineer**, not the implementer. Stop, think about what the task actually requires, write a crisp sub-agent prompt, then hand it off.

## Steps

1. **Understand the task** — clarify scope if ambiguous; ask one targeted question rather than proceeding blind.
2. **Draft the sub-agent prompt** — see format below. Think carefully: the sub-agent has no conversation context beyond what you write.
3. **Delegate** — call the `Agent` tool with the `{{ subagent_model }}` model and your crafted prompt.
4. **Review** — inspect the result; report a concise summary to the user. Apply or save the output as appropriate.

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
<any hard constraints: line limits, style rules, no new dependencies, etc.>
```

## Good candidates for /sub

- Generating repetitive code (test stubs, boilerplate, config)
- Drafting documentation or commit messages
- Transforming or reformatting data/text
- Contained analysis with a clear goal and bounded scope
- Tasks that require tool use (file reads, edits, shell commands, git ops) — a cheap agent handles tools fine
- Multi-step tasks where the steps are mechanical and the goal is unambiguous

## Bad candidates (handle yourself instead)

- Tasks so ambiguous that even you couldn't write a clear prompt for them
- Judgment calls that require weighing the full conversation history to decide correctly
- Tasks explicitly requiring Opus/Sonnet-tier reasoning (rare — default to delegating and only hold back if clearly warranted)

**Bias strongly toward delegating.** The failure mode to avoid is deciding a task is "too complex for a cheap agent" based on step count or tool use — that's often unnecessary. The question is whether the *prompt* you write is clear enough, not whether the agent can execute it.

## Model note

Sub-agents are spawned with the configured low-cost model. It should be fast and capable of multi-step tool use. Default to delegating; only handle the task yourself if you genuinely cannot write a prompt clear enough for a capable model to execute correctly.
