# OpenCode-specific Guidance

## Subagents

- Use only `github-copilot/gpt-5.6-luna` for delegated OpenCode subagents.
- Choose the configured agent role according to task complexity; do not substitute another provider or model.

## Python quality

- For edited Python files in projects with `pyproject.toml`, run the project's relevant `ruff` and `pyrefly` checks, plus targeted tests when behavior changes.
- Prefer the project's existing environment and lockfile.
- Use the narrowest relevant verification first, then widen it when the change affects runtime or integration behavior.
