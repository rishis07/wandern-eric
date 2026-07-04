# 0005 — Dashboard layout regroup

**Status:** done
**Date:** 2026-07-04

## Components affected
- [x] Frontend            (wandern-eric/)
- [ ] Backend logic       (python-backend/)
- [ ] GCS data schema     (data.json / aggregations.json keys)
- [ ] Production server   (RasPi — cron schedule, env, deploy)

## Why
Daily and hourly information is intermingled on the dashboard. Group blocks by
the question they answer (guilt trip → the year → this week → history) so each
row has one time horizon. Verdict prototyped and picked on 2026-07-04 (variant
"A · Grouped" vs current layout).

## Contract
New page order in `App.jsx`:
1. Projection alert (existing `day >= 20` gating unchanged)
2. Heatmap — **core rule: nothing goes above the heatmap except the alert**
3. "This week" row: WeekComparison (2/3) + Latest Activities (1/3)
4. "History" row: Monthly trend (2/3) + Step Stats (1/3)
5. Changelog

`Aggregations.jsx` stops being a layout container: split into
`ProjectionAlert.jsx` and `StepStats.jsx` (separate files, matching how
`components/` is organized); `Aggregations.jsx` is deleted and `Activities`
gets placed by `App.jsx` directly. No data shapes, JSON keys, or fetch URLs
change.

## In scope
- Reordering + regrouping in `App.jsx`.
- Splitting `Aggregations.jsx` into `ProjectionAlert.jsx` + `StepStats.jsx`.
- The two 2/3 + 1/3 grid rows, stacking to one column on mobile (as
  prototyped).

## Out of scope
- Any visual redesign of the individual components (colors, cards, chart
  styling stay as-is).
- Section header labels (rejected with prototype variant C).
- Changes to the alert visibility logic (stays gated to day ≥ 20).
- Deduplicating the `aggregations.json` fetches (after the split, four
  components fetch it independently; browser cache makes this a non-problem at
  this scale).
- `wandern-tests/` stays untouched.

## Acceptance criteria
- [x] Page renders in the order above; alert still only appears from the 20th
      of the month.
- [x] On `lg` screens the two rows show 2/3 + 1/3 side by side; on mobile they
      stack.
- [x] All data displayed is unchanged vs production (same numbers, same
      components).
- [x] `npm run lint` and `npm run build` pass.
- [x] Prototype files (`src/prototype/`, prototype entry in `App.jsx`) are
      deleted.

## Deployment steps
- [x] **Frontend** — push to `main` → GitHub Actions auto-builds & deploys to
      GitHub Pages / wandern-eric.de (first run failed transiently in
      deploy-pages status polling; verified live after re-run)
- [x] Update `Changelog.jsx` (user-facing changes)

## Open questions
(none)
