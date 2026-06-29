# 0002 — Activities module (latest workouts)

**Status:** done        <!-- shipped 2026-06-28, commit e71b294 -->
**Date:** 2026-06-29     <!-- backfilled after the fact -->

## Components affected
- [x] Frontend            (wandern-eric/)
- [x] Backend logic       (python-backend/)
- [x] GCS data schema     (new activities.json blob)
- [x] Production server   (RasPi — manual repo upload for the new backend code)

## Why
The dashboard showed only steps. Surface Eric's recent workouts (walks, bike,
treadmill) so the page reflects actual activity, not just a step count.

## Contract
- Source: `GET /users/me/dataTypes/exercise/dataPoints` (paginated via
  `nextPageToken`, `pageSize: 1000`), same Google Health OAuth session as steps.
  **Fetches all exercise points** — no date filter (see Design decisions).
- `consolidate_activities()` groups raw `exercise` points by `(local date,
  exerciseType)`, sums distance + duration, drops sessions shorter than
  `MIN_ACTIVITY_DURATION_SECONDS` (120s — the API surfaces stray ~4s sessions).
- Published artifact `activities.json` — a list of records, newest first:
  ```json
  {
    "date": "YYYY-MM-DD",
    "exercise_type": "<raw Google Health enum>",
    "label": "<API displayName>",
    "sessions": 1,
    "distance_km": 0.0,
    "duration_seconds": 0,
    "last_start_time": "<ISO local time>"
  }
  ```
- Only the `ACTIVITIES_TO_SHOW` (3) most recent are published.
- Uploaded **no-cache** (`Cache-Control: no-cache, max-age=0`), like
  `today.json`, so the CDN doesn't mask the hourly refresh.

## Design decisions
- **Query everything, no date filter.** `get_exercise_points()` pulls all
  exercise sessions and lets `consolidate_activities()` + `ACTIVITIES_TO_SHOW`
  trim to the latest 3. Chosen because personal-scale data fits in one or two
  pages, so the simplicity beats minimizing the payload.
- **A date filter IS available** if this ever needs to scale: the API accepts a
  `filter` query param, e.g.
  `{"filter": 'exercise.interval.civil_start_time >= "2026-06-25"'}`
  (explored in `python-backend/google_health_activities.ipynb`). Tested but
  intentionally not wired in.

## In scope
- Backend: `get_exercise_points()`, `consolidate_activities()`,
  `update_and_save_activities()`, called from `run_intraday()`.
- Frontend: `Activities.jsx` panel (icon + distance/duration), exercise-type
  SVG icons (`bike`, `treadmill`, `walk`, `default`), split the monthly trend
  into `StepsTrend.jsx`, rework `Aggregations.jsx` into a two-column band
  (step stats left, activities right).

## Out of scope
- Changing the steps `{date, count}` pipeline or `aggregations.json` keys.
- A separate cron job — activities refresh piggybacks on the hourly intraday run.
- Full activity history on the frontend (only the latest 3 are shown).

## Acceptance criteria
- [x] `activities.json` published from the hourly intraday run with the 3 most
      recent consolidated workouts.
- [x] Sub-120s stray sessions are dropped; same-day same-type sessions merged.
- [x] Distance shown in km (from `distanceMillimeters`), duration in seconds.
- [x] Frontend Activities panel renders with per-type icons; today's workouts
      appear within the hour (no-cache).

## Deployment steps
- [x] **Frontend** — pushed to `main`; GitHub Actions auto-deployed.
- [x] **Production server (RasPi)** — ⚠️ manual repo upload required: the new
      backend code (activities functions in `main.py`) only runs on the Pi after
      the repo is uploaded. No new crontab entry — the refresh rides the existing
      hourly intraday run once the code is present.
- [x] **GCS schema** — new `activities.json` blob; additive, no existing keys
      changed, so no frontend coupling broke.
- [x] Update `Changelog.jsx` (activities entry added).

## Open questions
- (none — shipped)
