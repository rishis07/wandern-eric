# 0003 — Week-over-week chart (this week vs last week vs typical)

**Status:** approved        <!-- draft → approved → done -->
**Date:** 2026-07-01

## Components affected
- [x] Frontend            (wandern-eric/ — new `WeekComparison.jsx`)
- [x] Backend logic       (python-backend/ — `calculate_aggregations()`)
- [x] GCS data schema     (one additive key in `aggregations.json`)
- [x] Production server   (RasPi — no cron/env change, but the new backend code must be uploaded to the Pi — see Deployment)

## Why
The dashboard shows totals and a monthly trend, but nothing answers "how is my
week going compared to normal?" A day-of-week chart with this week, last week,
and a typical week makes weekly pace and weekday patterns legible at a glance.

## Contract
The only *aggregation* is the typical-week average, so that is the only thing the
backend emits. Last week and this week are raw daily counts that already live in
`data.json` / `today.json`; the frontend selects (windows) them for display — it
does not recompute any metric.

- **`aggregations.json`** gains one additive key, the all-history mean steps per
  weekday (generalizes the existing `avg_by_day` that already backs
  `max_avg_dow` — expose all 7 days instead of only the max):
  ```json
  "avg_steps_by_weekday": [
    { "day": "Monday",    "steps": 6803.2 },
    { "day": "Tuesday",   "steps": 7112.9 },
    ... 7 entries, Monday-first, float mean
  ]
  ```
  Computed over every finalized day in `data.json`; days with no record are
  excluded from the mean (not counted as zero), matching the existing
  `avg_by_day` behavior. No existing keys change.
- **Frontend `WeekComparison.jsx`** fetches `aggregations.json`
  (`avg_steps_by_weekday`), `data.json` (last week + this week's finished days),
  and `today.json` (today's in-progress count), and renders a Recharts
  `ComposedChart`:
  - **average** → a line (the baseline / "typical week")
  - **last week** and **this week** → grouped bars per weekday
  - x-axis: Monday → Sunday. Weekdays this week that haven't happened yet have no
    bar (no dangling line).

## Design decisions
- **Average = all history.** Chosen so "average steps for a weekday" has a
  *single* definition in the backend (reuses `avg_by_day`); a trailing-N-weeks
  window would create a second, competing definition alongside `max_avg_dow`.
  ⚠️ **Revisit later:** an all-history mean will skew slowly as years accumulate
  or fitness changes, and won't reflect recent form. Acceptable now (little data,
  uncertain project lifetime); reconsider a trailing window if/when it matters.
- **Averaging is backend; week windowing is frontend.** The mean is the only
  transformation, so it lives in `calculate_aggregations()`. "Last week" / "this
  week" are raw daily counts already present in `data.json`/`today.json`;
  re-emitting them in `aggregations.json` would duplicate raw data, not derive a
  metric. Windowing raw points for display is presentation (same class as the
  heatmap's existing "last 365 days" slice), so it stays in the component.
- **Timezone-safe week window.** The frontend anchors the week on the latest
  *date present in the data* (`today.json`'s date, else the newest day in
  `data.json`) rather than the browser clock. Those dates are already
  Berlin-local, so no browser-timezone math is needed. Week starts Monday via a
  shared frontend helper (also reused by the heatmap fast-follow, spec TBD).
- **Today rides `today.json`, not the aggregation.** `data.json` doesn't change
  during the day, so `aggregations.json` stays a daily, cached artifact. The only
  value that moves intraday (today's count) comes from the already-hourly,
  no-cache `today.json` — the same merge `Heatmap.jsx` already does
  ("finalized wins; add today only if not yet finalized").

## In scope
- Backend: extend `calculate_aggregations()` to emit `avg_steps_by_weekday`
  (all 7 weekdays, Monday-first), reusing the existing `avg_by_day` groupby.
- Frontend: `WeekComparison.jsx` (ComposedChart: average line + this/last grouped
  bars); a shared "Monday-start week window" helper anchored on the data's latest
  date; add the component to the `App.jsx` layout.
- Update `Changelog.jsx`.

## Out of scope
- Changing `data.json` / `today.json` shapes or any existing `aggregations.json`
  key (the new key is purely additive).
- Making the heatmap start weeks on Monday — **fast-follow, separate spec**,
  contingent on whether `react-calendar-heatmap` supports a Monday start
  (unverified; likely not out of the box). The frontend week helper built here is
  reusable by it.
- Trailing / recency-weighted average windows (see Design decisions).
- Any new cron job or intraday recompute of `aggregations.json`.
- **Verifying the timezone of Google Health data (⚠️ potential future problem).**
  This spec *assumes* the daily step dates from Google Health are always keyed to
  Berlin-local days — the whole "timezone-safe week window" design leans on that.
  We do not currently know how the dailyRollUp assigns a date, or whether it is
  sensitive to Eric's physical location (e.g. while travelling across timezones a
  day could roll over at the wrong local midnight, mislabeling steps and shifting
  which week they fall in). Confirming/handling this is out of scope here but must
  be investigated before trusting week/day boundaries for a globe-trotting Eric.

## Acceptance criteria
- [ ] `aggregations.json` contains `avg_steps_by_weekday` with 7 entries,
      Monday-first, each the all-history mean for that weekday; existing keys
      unchanged (frontend `Aggregations.jsx` / `StepsTrend.jsx` still work).
- [ ] `avg_steps_by_weekday[day].steps` matches a hand-computed mean of that
      weekday's counts in `data.json` (missing days excluded).
- [ ] `WeekComparison.jsx` renders a Mon→Sun ComposedChart: average as a line,
      last week and this week as grouped bars.
- [ ] This week's not-yet-occurred weekdays show no bar; today's bar reflects
      `today.json` and updates within the hour (no-cache).
- [ ] Week windows are correct across a browser set to a non-Berlin timezone
      (anchored on data dates, not the browser clock).

## Deployment steps
- [ ] **Frontend** — push to `main` → GitHub Actions auto-builds & deploys to
      GitHub Pages / wandern-eric.de.
- [ ] **Production server (RasPi)** — ⚠️ NOT automatic: the new
      `calculate_aggregations()` code only produces `avg_steps_by_weekday` on the
      Pi after the repo is uploaded there. No crontab/env change — the daily run
      picks it up once the code is present.
- [ ] **GCS schema** — additive key only; regenerated on the next daily run (or a
      manual `run_daily`) so the frontend has data to read.
- [ ] Update `Changelog.jsx` (week-over-week chart entry).

## Open questions
- (none — approved)
