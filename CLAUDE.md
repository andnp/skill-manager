# Repository Guide

## What this repo is

`skill-manager` is a local Python CLI for maintaining agent skills, hooks,
prompts, and harness-specific agent instructions from one source repository.
It deploys those artifacts to Claude, Codex, Copilot, Agy, and OpenCode.

The project is source-first: this repository is authoritative, while files
under user home directories are generated or installed copies.

## Mental model

The normal flow is:

1. Source packages and templates live in this repository.
2. Manifests and variable files describe what belongs to each package.
3. Rendering applies harness-specific values and overlays.
4. Adapters map the rendered output to each harness's filesystem.

The GitHub workflow discovers skill packages, downloads selected packages into
the source tree, records selections in `state.yaml`, and can refresh them from
their current upstream branches.

## Important directories and files

- `src/skill_manager/` — CLI commands and application code.
- `src/skill_manager/cli.py` — command-line entry points and orchestration.
- `src/skill_manager/manifest.py` and `models.py` — source layout and domain models.
- `src/skill_manager/rendering.py` — variable substitution and agent composition.
- `src/skill_manager/adapters.py` — harness destination mapping.
- `src/skill_manager/sync.py` — deployment, export, listing, and extraction.
- `src/skill_manager/github.py` and `state.py` — remote discovery/import and saved selections.
- `skills/` — source skill packages; each package is independently deployable.
- `agents/` — source templates for globally deployed harness instructions.
- `tests/` — behavior-focused tests for the CLI and core workflows.
- `README.md` — user-facing command and layout documentation.
- `pyproject.toml` and `uv.lock` — project metadata, dependencies, and tooling.

## Source-of-truth rules

- Edit source files here, not generated copies under user home directories.
- Root `CLAUDE.md` and `AGENTS.md` are repo-local orientation files. They are
  intentionally not inputs to `skill-manager` deployment.
- `agents/shared.md` and harness overrides are different: they are source
  templates that `skill-manager deploy` uses for global agent files.
- Keep harness differences in adapters or harness overlays instead of copying
  shared behavior into every skill.
- Use `skill-manager deploy --dry-run` before a deployment that may affect
  global harness configuration.
- Treat installed skill copies as outputs. Use extraction deliberately when a
  deployed copy is meant to become source, rather than editing it casually.

## Development workflow

Use the existing environment and lockfile:

```bash
uv sync
uv run ruff check .
uv run pytest
```

When behavior changes, update the relevant tests and keep the test cases
focused on observable contracts. Inspect the README, project metadata, and
the nearest module/tests before making a change. Keep changes small and use
atomic conventional commits.

For deployment or GitHub changes, verify both the source result and the
destination behavior. `GITHUB_TOKEN` may be used for GitHub API access; never
commit credentials or generated private data.

## Where to start when changing something

- CLI behavior: start in `cli.py`, then follow into the owning module and its tests.
- Package discovery or layout: inspect `manifest.py` and `models.py`.
- Harness output or variables: inspect `rendering.py` and `adapters.py`.
- Deployment, export, or extraction: inspect `sync.py`.
- Remote installation or refresh: inspect `github.py` and `state.py`.

Prefer the narrowest relevant check first, then run the full existing suite
when the change crosses module or integration boundaries.
