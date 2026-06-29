# CLAUDE.md

Guidance for working in this repo. **Wandern Eric** is a personal step-tracking
pet project: it pulls daily step data from a fitness wearable, stores it as JSON
in a public Google Cloud Storage bucket, and renders a heatmap + aggregations in
a small React dashboard. It doubles as content for Eric's YouTube channel.

## Architecture / data flow

```
Raspberry Pi (cron)                 GCS bucket "wandern-eric-data"        GitHub Pages
python-backend/main.py  ──upload──▶  data.json + aggregations.json  ──fetch──▶  wandern-eric/ (React)
   (Fitbit API)                          (public, read-only)                    wandern-eric.de
```

1. `python-backend/main.py` fetches *yesterday's* steps from the Fitbit API,
   appends to `data.json`, recomputes `aggregations.json` (Pandas), and uploads
   both to the GCS bucket.
2. The frontend fetches those two JSON files directly from
   `https://storage.googleapis.com/wandern-eric-data/{data,aggregations}.json`
   — there is **no API server**. The bucket is public and the only contract
   between backend and frontend.

## Repo layout

- `wandern-eric/` — **the real, deployed frontend.** React 19 + Tailwind v4 +
  Vite (rolldown-vite). This is what ships to GitHub Pages / wandern-eric.de.
- `wandern-tests/` — **demo/teaching copy for Eric's YouTube channel**, showing
  the evolution of the frontend. Near-identical to `wandern-eric/`. NOT
  deployed, NOT git-tracked. Don't treat it as production; changes here are for
  video content only.
- `python-backend/` — Fitbit extraction + aggregation (Poetry, Python 3.12).
- `.github/workflows/deploy.yml` — builds **only** `wandern-eric/` and deploys
  `wandern-eric/dist` to GitHub Pages on push to `main`.

## Common commands

Frontend (run inside `wandern-eric/`, or `wandern-tests/` for video work):
```bash
npm install
npm run dev      # local dev server
npm run build    # production build -> dist/
npm run lint     # eslint
```

Backend (run inside `python-backend/`):
```bash
poetry install
poetry run python main.py    # fetch yesterday + reaggregate + upload to GCS
```

## Spec-driven development

Non-trivial work (features, migrations, schema/aggregation changes) starts with
a **spec** in `specs/` — agreed *before* code is written. See `specs/README.md`.

- Create one via `/spec <title>` — this **starts a discussion**, it does not
  infer a spec from the title. We converge through the template, then the file
  is written with `Status: approved`.
- **Specs are temporary** (alive while the work is in flight, then `done`);
  **this file (CLAUDE.md) is permanent** — promote durable lessons up here.
- The template's *Components affected* + *Deployment steps* exist to make sure
  every deploy path is followed — especially the ⚠️ manual RasPi upload, which
  isn't automatic.
- Skip specs for trivia (typos, dep bumps, renames).

## How things actually run (deployment)

- **Frontend:** auto-deployed by GitHub Actions on every push to `main`.
- **Backend:** runs on Eric's **Raspberry Pi via cron**. The repo is **uploaded
  to the Pi manually** whenever the extraction logic changes — which is rare.
  So backend changes don't deploy themselves; mention when a change requires a
  manual Pi update.

## Backend details

- Config is via `python-backend/.env` (see `.env-example`). Fitbit OAuth2
  client id/secret, redirect URI, GCP project/bucket.
- Fitbit OAuth tokens persist in `token.json`; `main.py` auto-refreshes expired
  access tokens (`FitbitController`).
- `calculate_aggregations()` produces: `max_steps`, `max_avg_dow`,
  `avg_per_month`, `avg_last_3_months`, and `prev_month_avg_to_eom_projection`
  (steps/day still needed to match last month's average). The frontend
  (`Aggregations.jsx`) depends on exactly these keys — changing the agg schema
  breaks the dashboard.

## In progress: Fitbit → Google Health API migration

Fitbit's Web API is being deprecated; Eric is migrating to the **Google Health API**
(`https://health.googleapis.com/v4`) — the server-to-server REST successor to the
Fitbit Web API. Migration is **in progress**: extraction is verified, not yet wired
into production.

- `python-backend/main.py` (Fitbit) is still the **live source of truth** on the Pi.
- `python-backend/google_health_api_migration.ipynb` — **the correct target, verified
  working.** `POST /users/me/dataTypes/steps/dataPoints:dailyRollUp` (scope
  `https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly`,
  `windowSizeDays: 1`) returns daily step totals; the notebook maps
  `rollupDataPoints[].steps.countSum` to the existing `{date, count}` record so the
  aggregations/GCS/frontend stay unchanged. Cross-checked vs production (6808 steps on
  2026-02-26 matched).
- ⚠️ **Dead ends — do NOT build on these:** `google_health_example.py` and
  `gh_migration.ipynb` use the **Google Fit REST API** (`fitness/v1`), which is **shut
  down end of 2026**. And "Health Connect" is Android, **on-device only (no cloud API)** —
  not usable from the Pi. Neither is a valid target. (This also resolves the old
  "what does the Fit `aggregateBy`/`bucketByTime` body do" question — moot now.)

Production swap (when ready): replace `FitbitController` with a `GoogleHealthController`
whose `get_daily_steps(date)` returns `{date, count}`; everything downstream is unchanged.
Note the `sedentary_minutes` field isn't in the Health API `steps` type (frontend doesn't
use it, so safe to drop). First OAuth needs a browser — do it once, then copy
`secrets/token_health.json` to the Pi (Google refresh tokens don't single-use-rotate like
Fitbit's, so the two-machine desync problem goes away).

## Secrets — IMPORTANT

The following live in `python-backend/` and are **untracked but unprotected**
(there is no `.gitignore` in `python-backend/` or at the repo root):
`.env`, `token.json`, `secrets/` (`client_secret.json`,
`application_default_credentials.json`), and `token_gh.json` (Google Health).

Do **not** `git add` these, and never run a blanket `git add .` / `git add -A`
from the repo root or `python-backend/` without checking. Consider adding a
`.gitignore` to protect them. Never print their contents.

## Conventions / gotchas

- The frontend reads from a hard-coded GCS URL; if the bucket name changes,
  update both `Heatmap.jsx` and `Aggregations.jsx`.
- Tailwind v4 (via `@tailwindcss/vite`) — no `tailwind.config.js`.
- React Compiler is enabled (`babel-plugin-react-compiler`); avoid patterns that
  break the rules of hooks.
- Keep `wandern-eric/` and `wandern-tests/` separate — don't "sync" them
  automatically; the divergence is intentional for video storytelling.
