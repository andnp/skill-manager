# Skill Manager

`skill-manager` keeps agent skills, hooks, and prompts in one repository and
deploys them to the coding harnesses you use every day.

The CLI is intentionally local and short-lived. It will support source-first
deployment, two-way extraction, GitHub discovery, and harness-aware templates.

## Development

```bash
uv sync
uv run skill-manager --help
uv run ruff check .
uv run pytest
```

The source repository uses `skills/<name>/` folders. Each skill can contain
its normal files plus an optional `skill-manager.json` variable file.
