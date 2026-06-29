# 0001 — Fitbit → Google Health API migration

**Status:** done        <!-- shipped 2026-06-21, commit 2f9e8e3 -->
**Date:** 2026-06-29

## Components affected
- [ ] Frontend            (wandern-eric/)
- [x] Backend logic       (python-backend/)
- [ ] GCS data schema     (data.json / aggregations.json keys)
- [x] Production server   (RasPi — cron schedule, env, deploy)

## Why
Fitbit's Web API is being deprecated. Step extraction must move to the Google
Health API (`https://health.googleapis.com/v4`), the server-to-server REST
successor, without disturbing the aggregations / GCS / frontend contract.

## Contract
- Endpoint: `POST /users/me/dataTypes/steps/dataPoints:dailyRollUp`
- Scope: `https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly`
- Request: `windowSizeDays: 1` (one day per rollup).
- Map `rollupDataPoints[].steps.countSum` → existing `{date, count}` record.
- Production swap: replace `FitbitController` with a `GoogleHealthController`
  whose `get_daily_steps(date)` returns `{date, count}`. Everything downstream
  (aggregations, GCS upload, frontend) is unchanged.
- `sedentary_minutes` is not in the Health API `steps` type — dropped (frontend
  doesn't use it).

## In scope
- New `GoogleHealthController.get_daily_steps(date) -> {date, count}`.
- One-time browser OAuth, then copy `secrets/token_health.json` to the Pi.
- Swapping the controller used by `main.py`.

## Out of scope
- ⚠️ **Google Fit REST API** (`fitness/v1`) — shuts down end of 2026.
  `google_health_example.py` and `gh_migration.ipynb` are dead ends; do NOT
  build on them.
- ⚠️ **Health Connect** — Android, on-device only, no cloud API. Not usable
  from the Pi.
- Any change to `aggregations.json` keys or the frontend.

## Acceptance criteria
- [x] `dailyRollUp` returns daily step totals matching production
      (6808 steps on 2026-02-26 cross-checked vs prod).
- [x] `GoogleHealthController.get_daily_steps(date)` returns the same
      `{date, count}` shape `FitbitController` did.
- [x] `main.py` runs end-to-end on the Pi against the Health API and uploads
      unchanged `data.json` / `aggregations.json`.

## Deployment steps
- [x] **Production server (RasPi)** — ⚠️ NOT automatic: did first OAuth in a
      browser, copied `secrets/token_health.json` to the Pi, uploaded updated
      repo, confirmed the cron run succeeds. (Google refresh tokens don't
      single-use rotate like Fitbit's, so the two-machine desync problem goes away.)
- [x] Update `Changelog.jsx` if the data source switch is user-facing.

## Open questions
- (none — extraction verified; remaining work is the production swap)
