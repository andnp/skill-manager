# Codex-specific Guidance

## Subagent reasoning

- Prefer `gpt-5.6-luna` with low reasoning for exploration, focused implementation, routine tests, and documentation.
- Use medium reasoning for work requiring more multi-step analysis or when a low-reasoning attempt leaves a specific issue unresolved.
- Use high reasoning selectively for ambiguous, cross-cutting, high-risk, security-sensitive, concurrency, migration, or difficult debugging work.

## Agent routing

- Use `explorer` for read-heavy investigation, `coder` for well-scoped implementation, and `complex_coder` for ambiguous or high-risk work.
- Assign coherent scopes that may span related commits; delegate by semantic ownership rather than commit count.
