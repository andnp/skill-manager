# Copilot-specific Guidance

## Subagent reasoning

- Use `gpt-5.6-luna` for delegated subagents.
- Choose low reasoning for bounded lookups, routine edits, and focused test work; medium for normal feature implementation, refactoring, and integration; high for cross-cutting changes, architectural decisions, concurrency, or difficult debugging.

## Language and tone

- Use plain, direct language. Do not try to sound smart or corporate.
- Prefer short, common words over jargon, inflated phrasing, needless qualifiers, and extra framing.
- Match the wording already used in the repository and by the user.
- Say what happened, what is uncertain, and what should happen next.
