# Shared Agent Guidance

## Scope and precedence

- Follow explicit user instructions first.
- Repository-local instructions and project configuration override this global guidance when they conflict.
- If this file is generated from a source repository, edit the source and redeploy it instead of hand-editing the generated copy.
- Do not let remembered context override current evidence or explicit instructions.

## Memory

- At the start of every task, before inspecting files, planning, editing, delegating, or doing other tool work, search the memory system with a concise task-specific query.
- Search results contain AI-generated summaries only; for every potentially useful result, read the full memory record with `read_memory` before relying on it.
- Read only records that are clearly relevant to the task or an active decision.
- Record durable findings such as root causes, decisions, constraints, verified behavior, and reusable patterns; do not record routine progress or unverified guesses.
- When a memory checkpoint reminder appears, record the thought before continuing or finishing.
- If the harness lacks the memory capability, state that limitation rather than silently skipping this requirement.

## Approach and communication

- Inspect before changing anything; make the smallest correct change.
- Preserve unrelated user changes and do not stage unrelated files.
- Avoid speculative compatibility code, error handling, or comments; add them when a concrete need or non-obvious WHY justifies them.
- Lead with the outcome. Keep responses concise, plain, and practical.
- State what happened, what is uncertain, and what should happen next.

## Exploration and documentation

- For architecture, symbol, flow, caller, or impact questions, start with codegraph when its index is healthy.
- Use codegraph exploration, search, callers, callees, impact, node, files, and status tools according to the question.
- Use local search and direct file reads for configuration, scripts, documentation, or when codegraph is unavailable or insufficient.
- If codegraph reports that the repository is not initialized, run `codegraph init` from the repository root and retry.
- Use the ragdocs MCP server for indexed documentation and git-history lookup when relevant; prefer document queries for documentation and git-history queries for rationale.
- Verify retrieved context against current files.

## Changes and verification

- Plan multi-step or risky work before editing; keep ownership and file boundaries clear.
- Use the project's existing environment and lockfile.
- For edited Python files in a project with `pyproject.toml`, run the relevant project lint, type, and test checks.
- Never run `ruff format`. `ruff check` and targeted autofixes are allowed.
- Verify changes with the narrowest relevant checks, then widen verification when runtime or integration behavior is affected.

## Git history and commits

Andy reviews commits, not branches. Each commit must be perfect on its own.

### Fixes and absorption

- In a GitButler workspace, every linting correction, type correction, bug fix, or error correction must be absorbed into the commit it fixes.
- Run `but absorb <file-id> --dry-run` first and accept the target only when it introduced the code being fixed.
- If the suggested target is wrong, investigate why and either fix the code location or split the work differently.
- Do not create separate fix commits for corrections to your own work.
- In non-GitButler repositories, use the repository's normal atomic commit workflow.

### Commit shape

- Keep commits tiny when possible: target no more than about 20 changed lines, counting additions and deletions; no minimum.
- If a coherent slice exceeds that budget, split it into independently valid slices; exceed it only when the changes cannot be separated safely.
- Use conventional commits: `type(scope): subject`; include a scope when it adds signal.
- Subjects are imperative, no longer than 72 characters, and contain no `and`; if the subject needs `and`, split the work.
- Include a brief WHY-focused body when the reason is not obvious; never put HOW in the body.
- Every commit must compile, lint cleanly, pass tests where applicable, and remain bisect-safe.
- Do not create broken intermediate states.
- Always rebase rather than merge when rewriting your own branch history.
- Getting history right is worth replaying work; do not rush past a bad split.

### Tests and splitting

- For a contract-breaking feature, bundle the required test fixes into the feature commit so tests are never broken between commits.
- For an additive feature, use a separate follow-on test commit when both commits remain independently valid.
- Repeated test breakage across feature commits signals coupling; consider a refactor that decouples the tests first.
- Some contract changes have no clean refactor; use one larger bundled commit instead of forcing an artificial split.
- For a large dirty worktree, plan the commit sequence first, then replay it step by step rather than staging a messy diff. Revert to `HEAD` only when the worktree contains only changes you own and the operation is safe.

## Version control and delegation

- Before executing any Git command, run `but status` to determine whether GitButler is active. Use GitButler commands only when it succeeds; otherwise use standard Git.
- Never add GitButler to a repository that is not already a GitButler workspace.
- Before implementation work, read the applicable `create-commit` skill when it is available.
- Use an explorer for read-heavy investigation, a coder for well-scoped changes, and a complex coder for ambiguous or high-risk work.
- Delegate independent read-heavy work in parallel when useful, but never have multiple agents edit the same files concurrently.
- The main agent owns requirements, final decisions, integration, and final verification.
