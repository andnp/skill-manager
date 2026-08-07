---
name: task-observer
description: "Review open skill-improvement observations from mcp-memory and make small, evidence-backed updates to the skill source tree."
---

# Task Observer

Use this skill only for the scheduled review of the skill-manager repository. The
source repository is the only code scope. The memory database is the canonical
observation store; do not create or maintain a Markdown observation log.

## Review workflow

1. Search mcp-memory for open observations with `search_memory_records`:
   - `status: "active"`
   - `tags: ["skill-observation"]`
   - add `skill:<name>` when reviewing one skill
   - use a concrete query such as `"skill improvement"` or terms from the observation title
2. Read only the matching records with `read_memory_record` before deciding what to change.
3. Inspect the current skill source under `skills/` and its nearby tests or metadata.
4. Apply an observation only when it has clear evidence, names an affected skill,
   and can be implemented as a small source-level change. Preserve existing
   behavior unless the observation directly supports changing it.
5. Keep edits limited to the affected `skills/<name>/` package. Do not edit
   `agents/`, daemon configuration, generated user files, other repositories, or
   unrelated skills. Do not commit, push, or run a user-level deployment.
6. Never copy private or internal details into a skill. Convert them into general
   guidance or defer the observation when that cannot be done safely.
7. If an edit was made and checked, resolve the observation with
   `resolve_skill_observation` using `resolution: "actioned"` and a note naming
   the source change. If it is not safe, specific, or in scope, use
   `resolution: "deferred"` with the reason. Do not resolve an observation merely
   because it was read.
8. If no observation meets these rules, make no edits and report a no-op.

## Guardrails

- Do not invent observations or infer a request from generic memories.
- Do not modify the memory schema, search behavior, skill-manager code, or daemon
  automation from this skill.
- Do not expose memory IDs, private notes, or database contents in source skills.
- Keep each review small enough to understand and verify in one run. A larger
  refactor must be deferred for explicit human review.

The daily automation validates the source tree and performs the user-level
deployment after this skill finishes.

## Attribution

This workflow is adapted from [one-skill-to-rule-them-all](https://github.com/rebelytics/one-skill-to-rule-them-all),
licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It
replaces that project's local observation log with structured mcp-memory records.
