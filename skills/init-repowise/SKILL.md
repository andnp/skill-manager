---
name: init-repowise
description: Initialize Repowise for a repository with the configured OpenCode GitHub Copilot model and Ollama embeddings. Use when the current repository is not already initialized with Repowise, or when the user explicitly asks to initialize or set up Repowise.
---

# Initialize Repowise

Initialize a repository-local Repowise wiki and index while leaving the
machine-wide editor and MCP configuration managed by `skill-manager`.

## Decide whether to initialize

- Work from the repository root.
- If `.repowise/` exists and the user did not explicitly request setup, run
  `repowise status` and report that the repository is already initialized.
- If the user explicitly requests initialization for an already initialized
  repository, clarify whether they want an incremental refresh (`repowise
  update`) or a full regeneration (`--force`) before choosing the destructive
  option.

## Initialize

Run this from the repository root:

```bash
repowise init \
  --provider opencode \
  --model opencode/github-copilot/gpt-5.6-luna \
  --embedder ollama \
  --prose \
  --yes \
  --no-editor-setup \
  --no-agents \
  --no-claude-md \
  --no-codex \
  --exclude .vscode/ \
  --exclude .mcp.json \
  .
```

The command uses the authenticated GitHub Copilot subscription through
OpenCode for prose generation and the local Ollama `qwen3-embedding:0.6b`
model for embeddings. Confirm the OpenCode connection and model first with
`opencode auth list` and `opencode models` if initialization fails there.

Do not remove `--no-editor-setup`: the global Claude, Codex, Copilot, and Agy
MCP entries are managed centrally by `skill-manager`. Do not add a hardcoded
repository path to the global Repowise MCP entry; `repowise mcp` uses the
current working directory when a harness starts it. The other `--no-*` flags
avoid creating project-local agent and MCP files that would duplicate the
global setup.

## Verify

After initialization, run:

```bash
repowise status
repowise doctor
```

Confirm that `.repowise/` exists, the configured provider is OpenCode, and the
embedder is Ollama. Treat any vector-store or provider failure reported by
`doctor` as a real follow-up issue; do not claim setup is fully healthy from a
successful process exit alone.

## Maintain the index

After substantial repository changes, run:

```bash
repowise update
```

Use `--resume` when an interrupted initialization offers a checkpoint. Use
`--force` only when the user explicitly wants the repository documentation
regenerated from scratch. `repowise mcp` needs no per-repository setup after
the global MCP deployment; invoke it from the repository root when testing the
MCP connection.
