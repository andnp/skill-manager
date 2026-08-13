# OpenCode-specific Guidance

## Subagents

- Use only `github-copilot/gpt-5.6-luna` for delegated OpenCode subagents.
- Choose the configured agent role according to task complexity; do not substitute another provider or model.

## Python quality

- Prefer the project's existing environment and lockfile.
- Use the narrowest relevant verification first, then widen it when the change affects runtime or integration behavior.
- Annotate function parameters.
- Do not annotate return types unless necessary, readability improves materially, or repository conventions require it.
- Avoid `Any`, `getattr`, `hasattr`, `typing.cast`, type-suppression comments, and other type-checker avoidance strategies; prefer protocols, typed interfaces, and explicit narrowing.
- Prefer absolute imports.
- Do not export names from `__init__.py` unless repository conventions already use that.
- Use self-documenting names; comments explain non-obvious reasoning only.
- Avoid Google-style docstrings unless repository conventions already use them.
- Avoid method/class docstrings unless complexity or public API requirements justify them.
- For Python projects using `uv` and Ruff, run `uv run ruff check --fix`; never run `ruff format`.
- Give every Python test a brief, multiline, human-readable docstring describing the test case.
