---
name: create-quality-jira-ticket
description: "Use when turning rough notes into a new Jira ticket, reviewing or rewriting an existing ticket draft, or preparing title, description, and acceptance criteria before filing. For broader Jira search, epic or duplicate scoping, issue updates, moves, comments, or creation workflow, use jira-manager."
---

# Create a Quality Jira Ticket

Turn rough notes into a clear Jira ticket, or tighten an existing draft without inventing missing facts. Pair with `jira-manager` when the task also needs Jira search, epic or duplicate scoping, or issue mutations.

## Choose the mode

- **Draft:** create a new ticket from notes or a problem statement.
- **Review:** assess and improve an existing draft while preserving its intent.
- **Create:** use `corecli jira` only after `jira-manager` has completed the relevant search and scoping work and the user has approved the draft.

## Workflow

1. Identify the desired outcome, affected workflow, user impact, and known constraints.
2. For Jira work in the RLCore repo, use `jira-manager` for context gathering, keyword search, semantic duplicate search, and epic selection before drafting.
3. Draft the ticket using the rules below. Surface uncertainty instead of filling gaps with guesses.
4. Return the result in this shape:

   ```text
   Title: <outcome-first title>
   Description: <one or two short paragraphs>
   Epic: <selected epic, recommendation, or none>
   Duplicate check: <what was checked and result>
   Notes: <only useful context or open questions>
   Acceptance criteria: <only when known or requested>
   ```

When context, epic choice, duplicate handling, or ticket boundaries are unclear, stop and surface the recommendation or question before creating the ticket. After explicit approval, use the approved `corecli jira` create flow and report the resulting key and link.

## Writing rules

- Lead with what needs to change and why it matters; ground claims in supplied or gathered evidence, and keep implementation ideas in notes only when they add useful context.
- Use a specific, outcome-first title. Include the affected workflow or user impact; omit story points, dates, and implementation details.
- Write for a reader who may not have the codebase open: describe user-visible behavior, workflow, data, and impact instead of implementation structure.
- Avoid function names, variable names, class names, file paths, module names, internal service names, and stack traces unless they are strictly necessary to identify an interface, compatibility boundary, or reproduction path.
- When a low-level identifier is necessary, explain its role in plain language rather than assuming the reader knows the codebase.
- Keep the description to one or two short paragraphs: explain the problem or desired outcome, then its impact, deliverable, relevant context, and key constraints.
- Use plain, direct language. Avoid filler, buzzwords, fake certainty, and consultant-style phrasing.
- Do not pad tickets with mirrored branches, checklists, or artifacts unless they are independently tracked planning units.
- Add acceptance criteria only when they are already known, requested, or obvious from the request. Do not invent formalities.
- Treat story points as rough planning signals, not promises. Include them only when requested or already supplied, and distinguish ideal engineering time from elapsed team time when estimating.

## Epic guidance

Prefer an epic that represents either:

- a large outcome that should be split into several tickets; or
- a coherent group of tickets sharing one outcome or theme.

Avoid vague buckets such as `Jira improvements`. A useful example is `Stabilize Jira sync hierarchy integrity`.

## Example

**Good**

Title: `Improve Jira sync reliability for parent links`

Description: Parent-link syncing sometimes fails silently, leaving issue relationships incomplete and roadmap reporting unreliable. Improve the sync flow so these failures are handled consistently and surfaced clearly.

**Avoid**

Title: `Jira 5pt - parent link backend fix`

Description: Update the parent-link handler, change the payload parser, add retries, and clean up logging.

The second version leads with implementation, hides the user impact, and puts an estimate in the title.
