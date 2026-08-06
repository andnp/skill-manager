---
name: create-quality-jira-ticket
description: "Use when turning rough notes into a new Jira ticket, reviewing or rewriting an existing ticket draft, or preparing title, description, and acceptance criteria before filing. For broader Jira search, epic or duplicate scoping, issue updates, moves, comments, or creation workflow, use jira-manager."
---

# Create a Quality Jira Ticket

Turn rough notes into a clear Jira ticket, or tighten an existing draft without inventing missing facts.

## Choose the mode

- **Draft:** create a new ticket from notes or a problem statement.
- **Review:** assess and improve an existing draft while preserving its intent.
- **Create:** use the available Jira workflow only after the draft, epic choice, and duplicate check are clear.

## Workflow

1. Identify the desired outcome, affected workflow, user impact, and known constraints.
2. For a new ticket, check the most relevant existing epic before drafting. If no epic fits, say so and recommend whether a new epic is warranted.
3. Check likely open or recent tickets for duplicates. Prefer reusing or updating a near-duplicate unless the requested outcome is clearly different.
4. Draft the ticket using the rules below. Surface uncertainty instead of filling gaps with guesses.
5. Return the result in this shape:

   ```text
   Title: <outcome-first title>
   Description: <one or two short paragraphs>
   Epic: <selected epic, recommendation, or none>
   Duplicate check: <what was checked and result>
   Notes: <only useful context or open questions>
   Acceptance criteria: <only when known or requested>
   ```

When epic choice, duplicate handling, or ticket boundaries are unclear, stop and surface the recommendation or question before creating the ticket.

## Writing rules

- Lead with what needs to change and why it matters; keep implementation ideas in notes only when they add useful context.
- Use a specific, outcome-first title. Include the affected workflow or user impact; omit story points, dates, and implementation details.
- Keep the description to one or two short paragraphs: explain the problem or desired outcome, then its impact and relevant context.
- Use plain, direct language. Avoid filler, buzzwords, fake certainty, and consultant-style phrasing.
- Add acceptance criteria only when they are already known, requested, or obvious from the request. Do not invent formalities.
- Treat story points as rough planning signals, not promises. Include them only when requested or already supplied; distinguish ideal engineering time from elapsed team time when estimating.

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
