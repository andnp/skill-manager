---
name: create-quality-jira-ticket
description: "Use when drafting a new Jira ticket from rough notes, shaping a stronger issue title and description, reviewing a Jira draft for clarity, or improving ticket quality before filing."
---

# Create a Quality Jira Ticket

Use this skill to turn rough notes into a clear new Jira ticket. The primary job is drafting a new issue, but it can also lightly review or tighten an existing draft.

## When to use

- Drafting a new Jira ticket from partial notes, chat scraps, or a quick problem statement
- Improving a weak Jira draft before it is filed
- Checking whether a ticket is clear enough for planning without over-writing it

## Core operating rules

1. Optimize for clarity, not completeness theater.
2. Write the ticket so someone can understand the problem and expected outcome quickly.
3. Emphasize **what** needs to change and **why it matters**.
4. Put implementation ideas in notes only when they are genuinely useful context.
5. Treat acceptance criteria as optional. Include them only when they are already known or obvious from the request.
6. Keep story points as planning signals, not promises.

## Preflight checks

Before drafting a new ticket, look for the most appropriate existing epic **first**. Do not create or reshape the ticket in isolation if it likely belongs under an epic. If no current epic fits, say so and consider recommending a new epic.

Also do a quick duplicate check: scan likely open or recent tickets and the likely epic for similar titles or outcomes. If a near-duplicate already exists, prefer updating or reusing it unless the new request is clearly a different outcome.

When epic choice, duplicate handling, or ticket boundaries are unclear, surface the recommendation or question to the user before creating or reshaping the ticket.

## Epic guidance

A good epic usually fits one of two shapes:

- A large multi-step task that is too big for one ticket and should break into several subtasks or follow-on tickets
- A set of related tickets that roll up to one shared outcome or theme

Avoid low-value bucket epics that are too vague, too broad, or just collect loosely related work without a clear outcome.

Example: good epic = `Stabilize Jira sync hierarchy integrity`; bad epic = `Jira improvements`.

## Story point guide

Use story points as rough planning guidance only. They are not delivery commitments, time promises, or a substitute for team discussion.

| Story points | Ideal engineering time | Elapsed / team time |
| --- | --- | --- |
| 1 | A few hours | Same day |
| 2 | About half a day to 1 day | 1-2 days |
| 3 | About 1-2 days | 2-4 days |
| 5 | About 2-4 days | 4-8 days |
| 8 | About 4-7 days | 1-2+ weeks |
| 13 | About 1-2 weeks | 2-4+ weeks |

Frame the estimate carefully:

- **Ideal engineering time** = focused hands-on implementation time if work goes smoothly.
- **Elapsed / team time** = real calendar time including review, QA, interruptions, dependencies, and coordination.

## Title rules

Write the title outcome-first, not component-first. Jira already has a component field, so the title should lead with the result or problem being addressed.

Preferred style:

- `Improve Jira sync reliability for parent links`
- `Reduce duplicate alert noise for failed nightly imports`

Title guidance:

- Lead with the improvement, fix, reduction, prevention, or enablement
- Include the affected workflow, user impact, or business problem
- Keep it specific enough to stand on its own
- Do not put story points, dates, or implementation details in the title

## Description rules

Keep the description to **1-2 short paragraphs** in most cases. If it is longer, tighten it. People stop reading walls of text.

A good description usually contains:

- **WHAT** is happening or needs to change
- **WHY** it matters to users, the business, support, planning, or reliability
- **NOTES** for useful context, constraints, or known unknowns

Keep implementation details out unless they are essential context. Prefer problem framing over solution narration.

Voice guidance:

- Use plain, direct, specific language with concrete nouns and verbs.
- Skip filler openings, padded formality, and generic AI phrasing. Avoid buzzwords like `leverage`, `robust`, `comprehensive`, `seamless`, or `strategic` unless they are literally accurate and necessary.
- Do not add fake certainty or overwrought adjectives when they do not add meaning. Write like a teammate describing a real problem to another engineer, not a consultant or marketing blurb.

A simple shape that works well:

- Paragraph 1: the problem or desired outcome
- Paragraph 2: why it matters, plus short notes if needed
- Optional acceptance criteria: only when already known

## Acceptance criteria

Acceptance criteria are optional. Include them when they are already known, requested, or genuinely helpful for defining done. Do not invent filler criteria just to make the ticket look formal.

## Anti-patterns to avoid

- Vague titles like `Jira bug`, `Parent link issue`, or `Backend cleanup`
- Component-first titles when the outcome should come first
- Descriptions that only describe implementation steps
- Descriptions with no concrete user, business, or problem framing
- Stuffing story points or estimates into the title
- Multi-paragraph essays that hide the actual point

## Examples

### Good

**Title:** `Improve Jira sync reliability for parent links`

**Description:** Parent-link syncing sometimes fails silently, which leaves issue relationships incomplete and makes roadmap reporting less trustworthy. We need the sync flow to handle these cases more reliably and surface failures more clearly.

This matters because delivery tracking and dependency views are only useful when parent-child relationships are accurate. Notes: most failures appear during bulk syncs and may be tied to inconsistent upstream payloads.

### Bad

**Title:** `Jira 5pt - parent link backend fix`

**Description:** Update the sync worker to refactor the parent-link handler, change the payload parser, add retries, and clean up logging.

Why it is bad: the title is vague, estimate-stuffed, and component-first; the description jumps straight into how without explaining the actual problem or value.
