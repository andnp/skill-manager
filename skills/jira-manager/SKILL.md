---
name: jira-manager
description: Use for Jira planning, searching, scoping, creating, updating, moving, transitioning, or commenting on issues; checking duplicates; and choosing epics, tasks, or bugs. Use with corecli jira and require approval before writes.
---

# Jira Manager

Coordinate Jira work with an advisory-first workflow: understand the work, search for existing issues, recommend the smallest useful shape, and present the draft before any mutation.

Use `corecli jira` as the authoritative interface for Jira operations in this repo. If the
global `corecli` entrypoint fails with a missing-dependency error, run it through the
repository-managed environment instead (e.g. `uv run corecli jira ...` from the `corecli`
repository).

When the task moves from search/triage to proposing or filing new ticket content, switch
to [create-quality-jira-ticket](../create-quality-jira-ticket/SKILL.md) for the actual
drafting — do not draft titles, descriptions, or acceptance criteria yourself. Search and
draft are separate phases with separate triggers: finishing the search phase does not cover
the draft phase. Keep file paths, function names, and raw stack-trace text out of proposed
ticket content unless strictly necessary for reproduction.

Keep Jira focused on real planning units. Do not mirror branches, checklists, or artifact trees unless they need independent tracking.

## Search before proposing

1. Read the relevant spec, notes, design docs, or `research_plan.md`; query memory for Jira conventions and task context.
2. Search for existing epics, issues, and likely duplicates with both forms:

   ```bash
   corecli jira search --project ENG --jql "..."
   corecli jira search-semantic --text "..." --issue-type Task
   ```

3. Phrase semantic searches a couple of ways so synonyms and older terminology are covered.
4. Inspect plausible matches with `corecli jira get ISSUE-KEY --json` and surface them before drafting new work.
5. Treat the project key as `ENG` unless the user explicitly names another project.

## Choose and present the shape

Recommend exactly one outcome unless the user asks for alternatives:

- Existing epic + task when the work belongs to an active stream.
- Standalone task for short, self-contained work.
- New epic + initial task only for multi-week, multi-owner, or multi-slice work.

Draft a concrete outcome-first title and a concise one- or two-paragraph description covering what, why, deliverable, and key constraints. Hold the draft when evidence is missing; do not invent facts or acceptance criteria.

Before any Jira mutation, show the recommendation, candidates considered, proposed titles, and draft content, then wait for explicit approval. After approval, use only the approved `corecli jira` create/update/move flows, preview writes with `--dry-run` when useful, and report resulting keys and links.

For batched description backfills or similar updates, request approval in batches of three or fewer.
