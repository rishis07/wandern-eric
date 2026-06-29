---
description: Work through a new spec with the user, then write the file
---

The user wants to spec out: "$ARGUMENTS"

Do NOT create a file yet. The spec file is the OUTCOME of a discussion, not a
guess from the title.

First, work through the spec interactively:
- Walk the sections of `specs/TEMPLATE.md` as a discussion, one topic at a time
  (Why → Components affected → Contract → In/Out of scope → Acceptance criteria
  → Deployment steps → Open questions).
- Use the template purely as the agenda of what must be covered.
- Challenge vague answers; ask about anything ambiguous.

Do not make assumptions. If you ever have to fill a gap with an assumption,
state it EXPLICITLY, label it clearly as an assumption, and treat it as an open
question until the user confirms it. Never silently bake a guess into the spec.

Only once we've converged AND there are no remaining open questions:
1. List `specs/` to find the highest existing NNNN; the new number is that + 1,
   zero-padded to 4 digits (start at 0001).
2. Make a slug from the title: lowercase, spaces → hyphens.
3. Write `specs/NNNN-<slug>.md` with the agreed content and `Status: approved`.
4. Show the user the result.
