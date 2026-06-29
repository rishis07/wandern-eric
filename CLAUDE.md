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

## Step extraction: Google Health API (migration done)

Extraction runs on the **Google Health API** (`https://health.googleapis.com/v4`),
the server-to-server REST successor to the deprecated Fitbit Web API. The migration
**shipped 2026-06-21** (commit `2f9e8e3`) — `FitbitController` is fully removed; the
Pi runs the Google Health code. See `specs/0001-google-health-migration.md`.

- `GoogleHealthController.get_daily_steps(date)` returns `{date, count}` via
  `POST /users/me/dataTypes/steps/dataPoints:dailyRollUp` (scope
  `https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly`,
  `windowSizeDays: 1`). Verified vs production (6808 steps on 2026-02-26 matched).
  The `{date, count}` contract is unchanged from the Fitbit era, so aggregations /
  GCS / frontend were untouched (the unused `sedentary_minutes` field was dropped).
- **Activities** (commit `e71b294`, see `specs/0002-activities-module.md`):
  `get_exercise_points()` + `consolidate_activities()` publish `activities.json`
  from the hourly intraday run.
- OAuth: token persists in `secrets/token_health.json`; `AuthorizedSession`
  auto-refreshes per request. First OAuth needs a browser, then copy the token to
  the Pi (Google refresh tokens don't single-use-rotate like Fitbit's did).
- ⚠️ **Dead ends — do NOT build on these:** `google_health_example.py` and
  `gh_migration.ipynb` use the **Google Fit REST API** (`fitness/v1`), **shut down
  end of 2026**. "Health Connect" is Android, **on-device only (no cloud API)** —
  not usable from the Pi.
- ⚠️ Known issue (README backlog): the daily append in `update_and_save_data` is
  **non-idempotent** — `run_daily` downloads prod `data.json`, appends yesterday,
  re-uploads, so running it twice duplicates a record. Matters for manual/test runs.

## Secrets — IMPORTANT

Secrets live in `python-backend/` and are now protected by
`python-backend/.gitignore` — it covers `.env`, `token.json`, `token_gh.json`,
`secrets/` (incl. `token_health.json`, `*client_secret*.json`,
`*credentials*.json`), and the generated `*.json` data files.

Still: there is **no root `.gitignore`**, so don't run a blanket `git add .` /
`git add -A` from the repo root without checking what it stages. Never `git add`
a secret, and never print their contents.

## Conventions / gotchas

- The frontend reads from a hard-coded GCS URL; if the bucket name changes,
  update both `Heatmap.jsx` and `Aggregations.jsx`.
- Tailwind v4 (via `@tailwindcss/vite`) — no `tailwind.config.js`.
- React Compiler is enabled (`babel-plugin-react-compiler`); avoid patterns that
  break the rules of hooks.
- Keep `wandern-eric/` and `wandern-tests/` separate — don't "sync" them
  automatically; the divergence is intentional for video storytelling.
