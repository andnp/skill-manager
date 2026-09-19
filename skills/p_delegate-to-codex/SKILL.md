---
name: delegate-to-codex
description: "Delegate an implementation task to the external Codex CLI (`codex exec`) running gpt-5.6-luna at low reasoning effort. EXPLICIT REQUEST ONLY — invoke solely when the user asks for Codex by name (\"ask codex to...\", \"have codex implement...\", \"delegate this to codex\"). Never invoke implicitly, and never as a substitute for the harness's built-in subagents or the `sub` skill."
---

# Delegate to Codex

Hand a concrete, bounded implementation task to the external Codex CLI. Your job is to
be the prompt engineer and the reviewer; Codex does the writing.

## Trigger boundary

Invoke this skill **only** when the user explicitly names Codex. Examples: "ask codex
to add the retry wrapper", "have codex implement this", "delegate that to codex".

Do not invoke it because a task looks delegable, because work should be parallelised,
or because a cheaper agent would do. For those, use the harness's built-in subagent
mechanism or the `sub` skill.

## Before delegating

1. **Settle the scope yourself.** Codex has no conversation history. Decide the goal,
   the file boundaries, the constraints, and what "done" means before writing a prompt.
   If the task is still ambiguous, resolve it with the user first — do not delegate an
   ambiguous brief and hope for the best.
2. **Confirm the commit plan.** If a commit plan is required by the repository's
   workflow, agree it before delegation and state it in the prompt, so Codex implements
   inside an already-approved scope instead of stopping at its own planning checkpoint.
3. **Decide what the task may touch** and say so in the prompt. Scope is enforced by a
   precise brief, not by flags.

## Running Codex

```sh
codex exec \
  -m gpt-5.6-luna \
  -c model_reasoning_effort="low" \
  "<delegation prompt>" 2>&1 | tee /tmp/codex-<task>.log
```

- `-m gpt-5.6-luna` and `-c model_reasoning_effort="low"` are both required. The user's
  `~/.codex/config.toml` sets a higher default reasoning effort, so the `-c` override
  must be passed on every invocation; omitting it silently runs a more expensive tier.
- If `codex` rejects the model identifier, report the missing capability rather than
  silently falling back to another model.

### Sandbox and permissions

Do not pass `-s/--sandbox`. Codex already resolves its sandbox from the user's
`~/.codex/config.toml`, which is deliberately configured. Overriding it from a delegation
command is how you break the task, not how you make it safer: tightening the sandbox to
`workspace-write` makes `.git` read-only, so any commit fails with
`Unable to create .git/index.lock`, and "fixing" that needs a
`sandbox_workspace_write.writable_roots` override to undo a restriction you introduced.

Constrain the delegate through an unambiguous brief — explicit in-scope paths, explicit
out-of-scope paths, and forbidden commands — not by fighting its configuration.

Use `-C <dir>` when the working root differs from the current directory, and
`--skip-git-repo-check` only when running outside a git repository.

### Capturing the output

`-o/--output-last-message` captures **only** Codex's final message, which is usually a
short summary — the substance of its work is in the transcript. Always redirect stdout
to a log (`| tee`) and read the log, or the deliverable is silently lost. Use `--json`
when you want to parse events programmatically.

### MCP side effects

Codex inherits every MCP server configured for it, and the sandbox governs the filesystem
and shell only — it does not gate MCP tool calls. A run can therefore write to memory
stores, issue trackers, chat, or email as a side effect of a task that never asked for it.

Do not disable Codex's MCP servers; they are configured on purpose and the delegate often
needs them. Instead:

- State in the prompt when the task must not write to any external system.
- Read the transcript for MCP tool calls after the run, and tell the user what Codex
  actually did — the side effects appear there and nowhere else, never in the final summary.

### Following up

```sh
codex exec resume <session-id> \
  -m gpt-5.6-luna \
  -c model_reasoning_effort="low" \
  "<follow-up: review findings, corrections, next slice>"
```

`codex exec resume` accepts a narrower flag set than `codex exec` (no `-s`, for example),
so prefer `-c key=value` overrides, which both accept.

Retain the session id from the first run; `codex exec` prints it as `session id: <uuid>`.
Prefer an explicit id over `--last` when other Codex sessions may have run. Use
`codex exec fork <session-id>` to branch an alternative approach from a shared setup.

## Prompt construction

Brief Codex like a capable colleague who just walked in with zero context:

```text
## Task
<one-sentence goal>

## Context
<repository, relevant file paths and symbols, prior decisions, constraints>
<verbatim snippets of anything small and load-bearing — Codex cannot read this conversation>

## Requirements
<the behaviour that must hold; explicit non-goals; the approved commit plan if any>

## Verification
<the exact commands to run, e.g. `uv run ruff check .` and `uv run pytest tests/foo.py`>

## Output
<what to return: changed files, a summary of each change, the check results>
<hard constraints: no new dependencies, no unrelated refactors, no writes to external systems>
```

Keep the brief tight. Low reasoning effort rewards an unambiguous, well-scoped task and
punishes a vague one; if you find yourself writing a prompt that needs Codex to make
architectural judgement calls, either settle those calls yourself first or use a more
capable delegate.

## After delegation

1. **Verify against the workspace, not the report.** Check `git status` / `but status`
   and the actual diff. A completion claim is not evidence.
2. **Run the checks yourself.** Do not trust reported test or lint results.
3. **Review the diff for scope creep** — unrequested refactors, speculative
   compatibility code, parallel implementations, or new dependencies. Remove them.
4. **Check shared files** (package initializers, barrel files, config) for overwrites
   rather than additions.
5. **Report honestly**: what Codex changed, what checks were run and their results, any
   MCP side effects observed in the transcript, and anything left unresolved.

You own the requirements, the integration, and the final verification. Codex is a
delegate, not an authority.
