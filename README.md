# Wandern Eric

Wandern Eric is a personal step-tracker that guilts me into walking.

> 🤖 Pair-programmed with Claudio (Claude), my AI intern. Most of the code
> here is being written by him. All design choices are made and owned by me.

Hi, my name is Eric and I spend 10 to 12 hours a day sitting at my desk. Doctors
might say that this is not healthy, but I don't really have a reason to get up.
Wandern Eric connects my watch data to a small dashboard so I can keep track of
how badly my sedentary life is affecting me.

Live at [wandern-eric.de](https://wandern-eric.de).

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://buymeacoffee.com/wanderneric)

## Architecture

Steps flow from a fitness watch to a public cloud bucket to a static dashboard.
For most of the dashboard there is no API server: the bucket is the only
contract between the backend and the frontend. The one exception is the free
"cheer" button, which does have a real API behind it — see Backend below.

```
Backend (cron)                      GCS bucket (public, read-only)          GitHub Pages
python-backend/main.py  --upload-->  data.json + aggregations.json  --fetch-->  wandern-eric/ (React)
   (Google Health API)               today.json + activities.json             wandern-eric.de
                                     cheers_aggregations.json

cheer-function/ (GCP Cloud Function)  --append-->  cheers/<YYYY-MM>.json  ---^
   POST /cheer, called directly by the frontend         (same bucket)
```

### Frontend
I asked Twitter for ideas and I got 100 options. I asked chatGePeTo and it told
me to use React + Tailwind with Vite. It's a little of an overkill, but the most
basic thing I wanted was the GitHub-style heatmap, which I found as a React lib.

React 19 + Tailwind v4 + Vite. Auto-deployed to GitHub Pages on every push to
`main`.

### Backend
Python (Poetry). A daily cron job pulls the previous day's steps from the Google
Health API, appends them to `data.json`, recomputes `aggregations.json` with
Pandas, and uploads both to the bucket. An hourly job publishes today's
in-progress steps (`today.json`), the latest workouts (`activities.json`), and
(as of the Support feature) a count of this month's free cheers
(`cheers_aggregations.json`). Runs as scheduled cron jobs on an always-on
machine.

Separately, `cheer-function/` is a small public GCP Cloud Function
(`POST /cheer`) the frontend calls directly to record a free cheer —
see `cheer-function/README.md`.

## Run your own

Everything here is reusable. What you need:

- A **Google Cloud project** with the **Google Health API** enabled, an OAuth
  consent screen, and an OAuth client (Desktop type) whose client-secret JSON you
  download.
- A **public GCS bucket** for the JSON data files, plus a **service-account key**
  (JSON) with write access to that bucket.
- An always-on machine with **Python 3.12** and **Poetry** to run the backend on
  a schedule.
- **Node.js** for the frontend.

### 1. Backend config

In `python-backend/`:

1. Copy `.env-example` to `.env` and fill in your GCP project, bucket, and the
   path to your service-account key.
2. Put your Google Health OAuth client secret at
   `python-backend/secrets/client_secret_health.json`.
3. Install deps and do the one-time authorization (opens a browser):
   ```
   poetry install
   poetry run python main.py --intraday --no-upload
   ```
   This writes `secrets/token_health.json`, which is reused and auto-refreshed
   afterwards. Your `.env`, `secrets/`, and the generated `*.json` files are all
   gitignored.

### 2. Server deploy

1. Copy `python-backend/` to the machine (git, `scp`, or `rsync`). Keep your
   `.env`, `secrets/`, and data `*.json` on the machine. If you authorized on a
   different computer, copy `secrets/token_health.json` over too (the first OAuth
   needs a browser).
2. `poetry install` on the machine.
3. Schedule it with cron. Example crontab (adjust the paths):
   ```
   # finalize yesterday's steps + recompute aggregations, once a day
   0 5 * * *    cd ~/wandern-eric && poetry run python main.py >> cron.log 2>&1
   # publish today's in-progress steps + latest activities, hourly during the day
   0 8-23 * * * cd ~/wandern-eric && poetry run python main.py --intraday >> intraday.log 2>&1
   ```
   The daily run (no flag) appends yesterday and is not idempotent, so run it
   once per day (see Known issues). `--no-upload` runs everything but skips the
   GCS writes, handy for testing.

### 3. Frontend config

1. Point the dashboard at your bucket: set `GCS_BUCKET` in
   `wandern-eric/src/lib/config.js`, the config file that points the frontend at
   your GCP bucket.
2. Let the browser read the bucket cross-origin. Apply a CORS policy that
   includes your dev and production origins, e.g. save this as `cors.json`:
   ```json
   [{ "origin": ["http://localhost:5173", "https://<you>.github.io", "https://your-domain"],
      "method": ["GET"], "responseHeader": ["Content-Type"], "maxAgeSeconds": 3600 }]
   ```
   then apply it: `gsutil cors set cors.json gs://your-gcs-bucket-name`.
3. Develop and build:
   ```
   cd wandern-eric
   npm install
   npm run dev      # http://localhost:5173
   npm run build    # -> dist/
   ```

### 4. GitHub Pages

The workflow at `.github/workflows/deploy.yml` builds `wandern-eric/` and deploys
`dist/` on every push to `main`. In the repo Settings > Pages, set the source to
**GitHub Actions**.

**Without a custom domain** (served at `https://<user>.github.io/<repo>/`):

- Set `base: '/<repo>/'` in `wandern-eric/vite.config.js` (it ships as `'/'`).
- Delete `wandern-eric/public/CNAME`.

**With a custom domain** (like wandern-eric.de, served at the root):

- Keep `base: '/'`.
- Put your domain (one line) in `wandern-eric/public/CNAME`.
- In Settings > Pages set the custom domain, and add DNS at your registrar: an
  apex domain needs A/AAAA records to the GitHub Pages IPs, a subdomain needs a
  CNAME record to `<user>.github.io`.

## Backlog / known issues
- **Daily append is not idempotent (low priority).** `update_and_save_data` in
  `python-backend/main.py` appends the day's record to `data.json` without checking
  whether that date already exists, so running the daily job twice for the same date
  creates a duplicate record that has to be deleted by hand. Easy fix: replace-or-insert
  by `date` (drop any existing record for that date before appending) so re-runs are safe.

- **Query Buy Me a Coffee coffee counts.** BMC's API (`developer.buymeacoffee.com`,
  `GET /v1/supporters`) returns each payment's `support_coffees` count and
  `support_created_on` timestamp. Plan: add it to the daily `python-backend`
  cron job (not a webhook), write a small stats file to the public bucket, and
  have the frontend display it in the Support section (`Cheer.jsx`). Needs an
  API access token stored like the other backend secrets.

## Out of scope (for now)

Deliberate non-goals. Doable, just not needed for a personal project today.

- **Not cloud-agnostic.** The backend uploads to Google Cloud Storage and the
  frontend reads straight from a GCS URL, so moving to another provider (S3, R2,
  and so on) would mean changing both. It could sit behind a small storage
  abstraction, but I don't need it right now.
- **Single data source.** Steps come only from the Google Health API. Another
  source (Garmin, for example) could plug in behind the same `{date, count}`
  contract, but I don't own a Garmin to build or test against.
