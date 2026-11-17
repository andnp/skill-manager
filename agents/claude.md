# Claude-specific Guidance

## Tool access

- Before any memory operation, load the memory search, record, and read tools with the Claude tool-discovery mechanism when they are not already available.
- Use the installed skill instructions for specialized workflows instead of assuming a fixed local path.
- Load `@RTK.md` when the Claude environment provides it.

## Claude workflow

- Keep Claude-specific command syntax and tool-loading details here; keep general task policy in `shared.md`.
- Always read a relevant installed skill before starting matching work, even when you believe you already know how to do it. Skills are not optional.

## Orchestration

- Act as an orchestrator: delegate implementation work to subagents unless the user instructs otherwise.
- Strongly prefer Haiku subagents (`model: "haiku"`); choose Sonnet or Opus only when you judge the implementation to be highly complex.
- When a subagent presents a commit plan and waits for approval, review it and approve it on the user's behalf so implementation continues.
