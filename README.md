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

## Commands

```bash
skill-manager init
skill-manager deploy [--skill NAME] [--harness claude] [--dry-run]
skill-manager list [--harness NAME]
skill-manager extract NAME [--harness NAME]
skill-manager discover OWNER/REPOSITORY
skill-manager install OWNER/REPOSITORY [--skill NAME]
skill-manager update
```

Use `skill-manager COMMAND --help` for complete options. `--root` selects a
different source repository and `--home` is useful for safe previews or tests.
The supported harness names are `claude`, `codex`, `copilot`, `agy`, and
`opencode` (with aliases for Copilot CLI and Antigravity).

Skills use Jinja-compatible Handlebars-style expressions such as
`{{ my_variable }}`. Values come from `skill-manager.json` in the skill folder
and select the matching harness key before falling back to `default`.

`discover` lists every `SKILL.md` package it finds and accepts a comma-separated
multi-selection by number, or `all`. After installation, selected repositories
and skills are saved in `state.yaml` at the source root:

```yaml
github:
  - repository: OWNER/REPOSITORY
    skills:
      - skill-name
```

Run `skill-manager update` to fetch the current default branch for every saved
repository and redeploy its selected skills. The local package is replaced so
files removed upstream are removed locally too.
