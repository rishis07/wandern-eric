---
description: Throwaway prototype to answer a design question before spec/code
---

A prototype is **throwaway code that answers a question**. The question:
"$ARGUMENTS"

Pick the branch by what's being asked:

- **"Does this logic feel right?"** → a tiny standalone script (backend: run
  with `poetry run python`; frontend logic: a scratch module exercised from the
  dev console). Print the full state after every step so the behavior is
  visible.
- **"What should this look like?"** → build several RADICALLY different
  variations of the page/component inside `wandern-eric/`, switchable via a URL
  search param (`?variant=a|b|c`) plus a small floating switcher bar, viewed
  with `npm run dev`. Real data comes from the GCS bucket like always — no
  mocks needed.

Rules:
- Throwaway from day one. Name files/components so a casual reader sees it's a
  prototype (`PrototypeLayoutA`, not `Layout`).
- ⚠️ **NEVER commit prototype code.** Pushing to `main` auto-deploys
  wandern-eric.de. Prototypes live in the working tree only and die there.
- Don't put prototypes in `wandern-tests/` — that copy is video content, not a
  scratch area.
- Skip the polish: no tests, no error handling beyond what makes it run.
- When the question is answered, capture the verdict where it belongs (the
  spec under discussion, or CLAUDE.md if it's a durable lesson), then delete
  the prototype code. The answer is the only keepsake.
