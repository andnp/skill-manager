---
name: document-search
description: Search local documentation, architecture guides, and commit history using the ragdocs MCP server. Use whenever searching for domain concepts, system design, architectural patterns, technical specifications, or git history rationale across indexed project corpora.
---

# Document Search with Ragdocs

Use the `ragdocs` MCP server for indexed documentation discovery, architecture lookup,
and historical commit rationale across local repositories and documentation sets.

## Choose the right tool

| Need | Tool | When to use |
|------|------|-------------|
| Documentation & architecture lookup | `query_documents` | Standard natural language questions, feature specs, API guides, component overviews |
| Vague or conceptual questions | `search_with_hypothesis` | HyDE query expansion when direct keywords or phrasing are uncertain |
| Historical rationale & decisions | `search_git_history` | Understanding WHY code or architecture changed, commit diffs, migration history |

## Effective tool usage

### `query_documents` (Hybrid semantic + keyword + graph search)

- **Query style:** Use descriptive natural language questions or precise technical phrases (e.g. `"event bus publish subscribe error handling"` rather than just `"bus"`).
- **Scope modes:**
  - `global` (default): searches across all indexed repositories and documents.
  - `active_project`: applies bounded ranking uplift to the current repository or `preferred_project`.
  - `explicit_projects`: hard-filters results strictly to `scope_projects` list.
- **Uniqueness & breadth:**
  - `uniqueness_mode="one_per_document"` (default): best for discovering distinct relevant documents.
  - `uniqueness_mode="allow_multiple"`: best when extracting all relevant sections from a single large spec or design document.
  - Increase `top_n` (up to 10–20) when surveying broad topics.

### `search_with_hypothesis` (Hypothetical Document Embeddings / HyDE)

- Generate a synthetic paragraph describing what the ideal documentation or design doc would say.
- The hypothesis is embedded directly into semantic space, matching documentation with similar meaning even if exact keywords differ.
- Use `project_context` or `project_filter` to target relevant repositories.

### `search_git_history` (Commit history and rationale)

- Use natural language queries describing the architectural change, bug fix, or refactor.
- Narrow scope with `files_glob` (e.g. `"src/pipeline/**/*.py"`) or `project_filter`.
- Set `include_diff=True` when inspecting the actual code diff associated with historical commits.
- Filter by `after_timestamp` / `before_timestamp` (Unix epoch seconds) when tracing specific regressions or release windows.

## Verification workflow

1. **Query ragdocs first** before resorting to manual file scans or brute-force `grep`/`rg`.
2. **Review chunk metadata** to identify canonical documents, source paths, and project IDs.
3. **Verify current state:** Ragdocs provides indexed context; always verify findings against active workspace files before editing.
