# <NNNN — short title>

**Status:** draft        <!-- draft → approved → done -->
**Date:** YYYY-MM-DD

## Components affected
<!-- check all that apply — this drives the Deployment section below -->
- [ ] Frontend            (wandern-eric/)
- [ ] Backend logic       (python-backend/)
- [ ] GCS data schema     (data.json / aggregations.json keys)
- [ ] Production server   (RasPi — cron schedule, env, deploy)

## Why
The problem or motivation in 1–3 sentences.

## Contract
The exact, checkable interface this change commits to:
- data shapes / JSON keys
- API endpoints + scopes
- function signatures
(Skip lines that don't apply.)

## In scope
- ...

## Out of scope
- ...        <!-- this section is what kills dead ends -->

## Acceptance criteria
- [ ] concrete, verifiable bullets ("6808 steps on 2026-02-26 matches prod")
- [ ] ...

## Deployment steps
<!-- fill in only the rows for components checked above; delete the rest -->
- [ ] **Frontend** — push to `main` → GitHub Actions auto-builds & deploys to GitHub Pages / wandern-eric.de
- [ ] **Production server (RasPi)** — ⚠️ NOT automatic: manually upload repo to the Pi; update crontab / env as needed; confirm the new schedule runs
- [ ] **GCS schema** — frontend reads exact keys; if keys changed, update `Heatmap.jsx` / `Aggregations.jsx` in the same change
- [ ] Update `Changelog.jsx` (user-facing changes)

## Open questions
- ...        <!-- must be empty before Status: approved -->
