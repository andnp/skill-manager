# Language-Scoped Agent Instructions

Status: implemented incrementally

## Purpose

`agents/shared.md` and `agents/<harness>.md` remain the source for universal
and harness-specific global guidance. Language-scoped guidance lives in
`agents/rules/<name>.md` and is projected into each harness format that can
represent its activation patterns.

## Source format

Each rule is Markdown with neutral `patterns` frontmatter:

```markdown
---
patterns:
  - "**/*.py"
---

Run Ruff, Pyright, and Pyrefly against the entire repository.
```

The loader validates that `patterns` is a non-empty list of non-empty
strings. Rule content can use the same variables as the global agent files
through `agents/skill-manager.json`.

## Deployment matrix

| Harness | Managed output | Scope support |
|---|---|---|
| Claude | `~/.claude/rules/<name>.md` | Native `paths` frontmatter |
| Copilot | `~/.copilot/instructions/<name>.instructions.md` | Native `applyTo` frontmatter |
| OpenCode | `~/.config/opencode/skill-manager/rules/<name>.md` plus `opencode.json` | Configured instruction paths |
| Agy | Repository-local `.agents/rules/<name>.md` | Native `trigger: glob` export |
| Codex | Repository-local nested `AGENTS.md` | Directory scopes only |

Codex export rejects extension globs such as `**/*.py` because a nested
`AGENTS.md` cannot preserve that file-level scope. Directory patterns such as
`src/**` are exported to `src/AGENTS.md`.

## Commands

Global native deployment:

```shell
skill-manager deploy --dry-run
skill-manager deploy --harness claude --harness copilot --harness opencode
```

Repository-local rules:

```shell
skill-manager export-agents --repo PATH --harness agy
skill-manager export-agents --repo PATH --harness codex
```

`export-agents` refuses conflicting destination files. It does not overwrite
repository-owned rules with different content.

## Ownership and cleanup

Global scoped-rule deployments record generated paths in
`.skill-manager/agent-rule-receipts.json`. A later deployment removes only
paths previously recorded by `skill-manager`; unrelated user rules and
configuration entries are preserved. Dry runs report cleanup without mutating
files or receipts.

Repository-local exports currently preserve stale files. Cleanup for those
exports requires an ownership format that does not conflict with checked-in
`AGENTS.md` files and remains future work.

## Compatibility rules

- Existing shared and harness override files remain supported.
- Rules without a native or safe hierarchical projection are rejected rather
  than silently widened to global scope.
- Harness-specific output formatting stays in rendering and adapter layers.
- User configuration is read, merged, and preserved; managed entries are
  removed only when their paths are recorded as skill-manager-owned.
