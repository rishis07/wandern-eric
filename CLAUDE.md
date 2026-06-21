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

## In progress: Fitbit → Google Health migration

Fitbit accounts are being deprecated (~end of May 2026) in favor of Google
Health / the Google Fitness API. Migration is **in progress**:

- `python-backend/main.py` (Fitbit) is still the **live source of truth** on the Pi.
- `python-backend/google_health_example.py` — working Google Fitness extraction
  (OAuth2 + `users().dataset().aggregate()`), built with Copilot's help. The
  **test works**, but is not yet wired into the production pipeline.
- `python-backend/gh_migration.ipynb` — migration scratch/exploration notebook.

**Open question Eric wants resolved (don't lose this):** the Google Fitness
`aggregateBy` request "filters" in `google_health_example.py` are not yet
understood — specifically what `dataTypeName`
(`com.google.step_count.delta`), the `dataSourceId`
(`derived:...:estimated_steps`), and `bucketByTime` actually select and how they
combine. It "just works" and that's unsatisfying. When touching this code,
prefer explaining/citing the official Google Fitness REST docs over adding more
unexplained magic.

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
