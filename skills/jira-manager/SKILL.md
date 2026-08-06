---
name: jira-manager
description: Use for Jira planning, searching, scoping, creating, updating, moving, transitioning, or commenting on issues; checking duplicates; and choosing epics, tasks, or bugs. Use with corecli jira and require approval before writes.
---

# Jira Manager

Coordinate Jira work with an advisory-first workflow: understand the work, search for existing issues, recommend the smallest useful shape, and present the draft before any mutation.

Use `corecli jira` as the authoritative interface for Jira operations in this repo. For ticket wording and draft review, also use [create-quality-jira-ticket](../create-quality-jira-ticket/SKILL.md).

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
