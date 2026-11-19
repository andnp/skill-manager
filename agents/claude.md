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
- **Do NOT use Opus or Sonnet subagents unless the user specifically asks. Use only Haiku subagents (`model: "haiku"`).**
- When a subagent presents a commit plan and waits for approval, review it and approve it on the user's behalf so implementation continues.
- When a subagent finishes, read its full diff carefully before pushing or opening a PR; never pass its work on from its report alone.
