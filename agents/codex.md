# Codex-specific Guidance

## Subagent reasoning

- Prefer `gpt-5.6-luna` with low reasoning for exploration, focused implementation, routine tests, and documentation.
- Use medium reasoning for work requiring more multi-step analysis or when a low-reasoning attempt leaves a specific issue unresolved.
- Use high reasoning selectively for ambiguous, cross-cutting, high-risk, security-sensitive, concurrency, migration, or difficult debugging work.

## Agent routing

- Use `explorer` for read-heavy investigation, `coder` for well-scoped implementation, and `complex_coder` for ambiguous or high-risk work.
- Assign coherent scopes that may span related commits; delegate by semantic ownership rather than commit count.

## Memory

- Treat an ongoing conversation as one task; do not search memory again for follow-up questions, clarifications, approvals, or status messages.
- Search memory only when a genuinely new substantive task begins or a memory checkpoint requires it.

## Python quality

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
