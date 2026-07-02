# 0004 — Custom heatmap (Monday-start), replacing react-calendar-heatmap

**Status:** done        <!-- implemented & verified 2026-07-02 -->
**Date:** 2026-07-02

## Components affected
- [x] Frontend            (wandern-eric/ — Heatmap rewrite, new component, temp compare page)
- [ ] Backend logic       (python-backend/)
- [ ] GCS data schema     (data.json / aggregations.json keys)
- [ ] Production server   (RasPi)

## Why
`react-calendar-heatmap` (1.10.0) hardcodes a Sunday-first grid: it has no
week-start prop, and row placement is `getStartDate().getDay()` based (0 =
Sunday). The German convention is Monday-first. We replace it with a small custom
SVG heatmap, which fixes the week start and drops the dependency. A temporary
side-by-side comparison page lets us verify visual parity before switching.

## Contract
Reproduce the current heatmap behavior exactly, with one change (week start).

- **Data pipeline (unchanged):** fetch `data.json` (required) + `today.json`
  (optional) from `DATA_BASE_URL`, merge with "finalized wins; add today only if
  it isn't finalized yet."
- **Window:** rolling last 365 days through today.
- **Color scale (unchanged):** reuse the `.color-scale-0..6` CSS in `index.css`,
  same thresholds — `null → 0`, `<=1000 → 1`, `<=2500 → 2`, `<=5000 → 3`,
  `<=7500 → 4`, `<10000 → 5`, else `6`; plus the `color-scale-intraday` outline
  when `value.intraday`.
- **Tooltips (unchanged):** `react-tooltip`, id `walking-heatmap-tooltip`, content
  `"<date>: <count> steps"` with `" (so far today)"` appended for intraday cells.
- **Labels:** month labels along the top, weekday labels (Mon/Wed/Fri) on the left.
- **Change:** columns run **Monday (top) → Sunday (bottom)**, using `weekdayIndex`
  from `src/lib/week.js`.

## Design decisions
- **Build, don't swap.** Libraries that support a Monday start exist
  (`@zi0w/calendar-heatmap`, `shadcn-heatmap`, `react-activity-calendar`), but a
  custom SVG grid is a small, well-understood amount of code, reuses what we
  already have (`week.js`, the color-scale CSS, `react-tooltip`), removes a
  dependency rather than adding one, and gives full control over the intraday
  cell and labels.
- **Presentational split.** The rendering lives in a `StepHeatmap` component that
  takes `data` + the date window as props. `Heatmap.jsx` does the fetch and wraps
  it; the comparison page feeds the same fetched data to both implementations.
- **Verify before switching.** `react-calendar-heatmap` stays installed through
  the comparison. Removing it and the compare page is the LAST step, after
  sign-off.

## In scope
- New `StepHeatmap` presentational component (custom SVG, Monday-first grid,
  month + weekday labels, color-scale classes, intraday outline, react-tooltip).
- Rewrite `Heatmap.jsx` to fetch (as today) and render `StepHeatmap`.
- Temporary **dev-only comparison page**: `wandern-eric/compare.html` +
  `src/compare.jsx` rendering both the old `react-calendar-heatmap` (Sunday) and
  the new `StepHeatmap` (Monday) from one shared dataset, at
  `http://localhost:5173/compare.html`. Not a production build input, so it never
  deploys.
- After sign-off: remove `react-calendar-heatmap` (dependency + its CSS import)
  and the comparison page.
- Update `Changelog.jsx`.

## Out of scope
- Any `data.json` / `today.json` / `aggregations.json` or backend change.
- Moving the count→color thresholds to the backend (they stay in the component
  for now; noted as latent frontend business logic).
- Palette changes or restyling beyond matching the current look.
- Other components.

## Acceptance criteria
- [x] Comparison page renders the current and new heatmaps from identical data;
      Eric confirms they match (colors, cell size/gutter, month + weekday labels,
      tooltips) apart from the intended Monday start.
- [x] New heatmap grid runs Monday (top) → Sunday (bottom).
- [x] Color buckets + `color-scale-intraday` outline match the current thresholds.
- [x] Tooltip text is identical (`"<date>: <count> steps"`, `+ " (so far today)"`).
- [x] Today's in-progress cell appears from `today.json`; finalized data wins.
- [x] Rolling ~365-day window; month + weekday labels present.
- [x] After sign-off: `react-calendar-heatmap` removed from `package.json`, the
      compare page deleted, `npm run build` + `npm run lint` pass.

## Deployment steps
- [x] **Frontend** — push to `main` → GitHub Actions auto-builds & deploys to
      GitHub Pages / wandern-eric.de. The comparison page is not a build input, so
      it does not ship.
- [x] Update `Changelog.jsx` (Monday-start heatmap).

## Open questions
- (none — approved)
