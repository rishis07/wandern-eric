# Specs

Spec-driven development for Wandern Eric. A **spec** is a short document that
settles *what we're building and how we'll know it's right* **before** any code
is written. The code is then written to satisfy the spec.

## Why bother

Most wasted work dies cheaply on paper. The committed Google Fit dead ends
(`google_health_example.py`, `gh_migration.ipynb` — both built on a shut-down
API) are exactly what a spec's **Out of scope** section prevents.

## Lifecycle

```
draft  ──►  approved  ──►  (implement)  ──►  done
  │            │                              │
write it &   you sign off on               verified against
resolve all  intent + acceptance           acceptance criteria;
open Qs      criteria                       durable lessons → CLAUDE.md
```

- **Specs are temporary.** They're alive while the work is in flight, then
  marked `done` as a historical record.
- **CLAUDE.md is permanent.** Anything durable you learn (a new rule,
  architecture fact, gotcha) gets promoted up into CLAUDE.md.

## When to write one

Test: *"Would I benefit from thinking this through before I start?"*

- ✅ A feature, a migration, a new aggregation, a schema change.
- ❌ Typos, dependency bumps, a renamed variable. Just do those.

A large effort can be one spec with phased acceptance criteria, or split into
several when the pieces ship separately.

## How to create one

Type `/spec <title>` (or just say "let's spec out X"). That **starts a
discussion** — it does not write a file from a title. We work through the
template together, resolve every open question, and only then is the file
written as `NNNN-<slug>.md` with `Status: approved`.

Two modes: if the design was already hashed out in the session, the spec is
**synthesized** from that discussion and confirmed (no re-interview). Otherwise
it's an **interview** — one question at a time, each with a recommended answer,
and anything the codebase can answer is looked up instead of asked.

## Files

- `TEMPLATE.md` — copy of the structure every spec follows.
- `NNNN-<slug>.md` — individual specs, numbered sequentially from `0001`.
