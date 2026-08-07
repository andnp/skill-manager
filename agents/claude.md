# Claude-specific Guidance

## Tool access

- Before any memory operation, load the memory search, record, and read tools with the Claude tool-discovery mechanism when they are not already available.
- Use the installed skill instructions for specialized workflows instead of assuming a fixed local path.
- Load `@RTK.md` when the Claude environment provides it.

## Claude workflow

- Keep Claude-specific command syntax and tool-loading details here; keep general task policy in `shared.md`.
