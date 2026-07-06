# 0006 — Support (free cheer + Buy Me a Coffee)

**Status:** done        <!-- shipped 2026-07-06, commit babbf50 (+ live GCP infra: cheer-function deploy, Pi upload) -->
**Date:** 2026-07-05 (last revised 2026-07-06)

> **Revision note:** the design changed significantly during implementation.
> The original interview-drafted version had a country dropdown
> (anonymous/share-country choice) and a public top-5-countries-this-month
> leaderboard. Both were dropped mid-build in favor of automatic server-side
> IP geolocation (never shown publicly) and a much simpler monthly counter,
> and a Buy Me a Coffee link was added as the primary CTA. This revision
> reflects what was actually built. **Everything below is live in production.**

## Components affected
- [x] Frontend            (wandern-eric/) — done
- [x] Backend logic       (python-backend/) — `update_cheer_aggregations()`, hooked into the existing hourly `run_intraday()`
- [x] GCS data schema     (new files: `cheers/<YYYY-MM>.json`, `cheers_aggregations.json`)
- [x] Production server   (RasPi) — python-backend changed, needs the ⚠️ manual upload (see Deployment steps)
- [x] **New component (not in template checklist):** a small public Python Cloud Function (`POST /cheer`), the project's first writable backend surface — deployed and live, `cheer-function/`

## Why
Give viewers of the wandern-eric dashboard two ways to show support: a free,
no-signup "cheer" (an engagement signal / content beat for Eric's YouTube
channel), and a paid Buy Me a Coffee link (one-time or membership) that
actually helps cover the Raspberry Pi and domain costs. The paid option is
the **primary** call to action in the UI; the free cheer is secondary
("or, cheer for free").

Both sides carry the same pitch, in first person: "I'll walk 100 extra steps
for you" (free) / "I'll walk 1,000 extra steps for you" (coffee) — a playful
pledge tied to the dashboard's actual subject (step tracking), and a natural
hook for LinkedIn content.

## Contract
- **Endpoint:** Python HTTP Cloud Function, `POST /cheer`, **no request
  body** — the client never selects or sends a country.
  - Response: `200 {"ok": true}` on success.
  - The function geolocates the request IP server-side (ipapi.co) to a
    country code for internal bookkeeping, then **discards the raw IP
    immediately** — only the country code is persisted. Deliberate
    privacy/legal choice: raw IPs are personal data under GDPR and would need
    a consent flow and retention policy; a bare country code isn't.
  - CORS: allow `POST` from `https://wandern-eric.de`,
    `https://wandern-eric.github.io`, `https://rishis07.github.io`,
    `http://localhost:5173` (same origins as the bucket's `cors.json`, but
    that file itself is unchanged — it only governs GET on the bucket).
- **Cheer log**, in the existing public `wandern-eric-data` bucket, one file
  per calendar month: `cheers/<YYYY-MM>.json` (e.g. `cheers/2026-07.json`) —
  append-only array of
  `{"timestamp": "<ISO8601>", "country": "<code>|null", "source": "organic"}`
  (`country: null` if geolocation fails). Per-month files (rather than one
  ever-growing log) so both the Cloud Function's append and the monthly
  count only ever touch one small file. Written only by the Cloud Function's
  service account, IAM-scoped to the `cheers/` prefix only (not the whole
  bucket). `source` exists for future extensibility — count logic (below)
  reads `len()` of the file regardless of `source` value, so it's
  forward-compatible with anything that appends differently-sourced entries
  to this file later.
- **`cheers_aggregations.json`** — `{"month": "YYYY-MM", "count": <int>}`.
  **Not** computed by the Cloud Function — instead, `python-backend/main.py`'s
  `update_cheer_aggregations()` reads the current month's `cheers/<YYYY-MM>.json`,
  counts entries (`len()`, no timestamp filtering needed since the file is
  already scoped to that month), and publishes the result. Hooked into the
  existing hourly `run_intraday()` cron, so the frontend's count is
  refreshed roughly hourly, not instantly on every cheer.
- **Concurrency:** the Cloud Function is deployed with
  `--max-instances=1 --concurrency=1` (see `cheer-function/README.md`), which
  serializes every invocation globally so no two requests ever run at once.
  `_append_cheer` additionally keeps a generation-match read-append-write
  retry loop as defense-in-depth, in case those deploy flags are ever
  dropped in a future redeploy.
- **Buy Me a Coffee:** a plain outbound link to
  `https://buymeacoffee.com/wanderneric` (`lib/config.js` →
  `BUY_ME_A_COFFEE_URL`) — no BMC JS widget (avoids a third-party script), no
  backend involvement.

## In scope
- Cloud Function: geolocate + append to `cheers/<YYYY-MM>.json`.
- `python-backend`: `update_cheer_aggregations()`, run hourly via `run_intraday()`.
- New GCS objects (above), public-read (matches existing bucket ACL); the
  cheer log's write access is restricted to the Cloud Function's service
  account, scoped to the `cheers/` prefix.
- Frontend (done) — `components/Cheer.jsx`, rendered as a standalone
  `#support` section near the bottom of `App.jsx` (before `Changelog`), plus
  a small "👏 Support" button next to the "Wandern Eric" h1 that
  smooth-scrolls to it (doesn't violate the specs/0005 "nothing above the
  heatmap except the alert" rule — it's inline with the header, not a new
  row):
  - Buy Me a Coffee button (primary) with the "I'll walk 1,000 extra steps
    for you ☕ — plus it helps cover the Raspberry Pi and domain..." copy.
  - A single free "👏 Support" button (secondary) with "I'll walk 100 extra
    steps for you 👏" copy, next to the current month's count ("X people
    supported this month").
  - Per-browser softening via `localStorage`: after cheering once, the
    button is replaced with "Thanks for the support! 🎉" (not a security
    control — just avoids the "why did my click do nothing new" confusion).
    **Expires at the start of each calendar month** (the stored value is the
    month cheered in, e.g. `"2026-07"`, compared against the current month —
    not just a bare flag), matching the monthly counter it softens the UI
    around, so a returning visitor next month can cheer again. Clearing
    storage resets it early.
- CORS configuration for the Cloud Function.

## Out of scope
- Country/geographic display of any kind — the Cloud Function collects a
  country code, but it is **not shown anywhere on the dashboard**. No
  dropdown, no leaderboard, no manual country selection by the user.
- Rate limiting / spam / abuse prevention of any kind — explicitly deferred;
  v1 ships without it.
- Querying Buy Me a Coffee's API for real coffee counts (`GET /v1/supporters`)
  — tracked in `README.md` → Backlog, planned as a daily `python-backend`
  cron addition, not part of this spec.
- Patreon integration / "monthly contributors" display — separate, later
  spec, not started.
- Any reaction types beyond the single free cheer (no free text, no emoji
  picker, no messages).
- Historical cheer trends or charts beyond the current month's count.
- Accounts/auth of any kind.

## Acceptance criteria
- [x] Buy Me a Coffee button renders and opens `https://buymeacoffee.com/wanderneric`
      in a new tab.
- [x] Free "👏 Support" button, monthly count display, and the "Thanks!"
      softening render correctly in the frontend against the dev mock.
- [x] Clicking "👏 Support" POSTs to the function with no body;
      `cheers/<YYYY-MM>.json` gets a new `{timestamp, country}` entry —
      verified directly against the live endpoint.
- [x] The Cloud Function never persists the raw IP anywhere (verified by
      reading `main.py` — only `country` is written). Geolocation confirmed
      working end-to-end (one live test returned `null` — a cold-start
      transient, not a bug — a later one correctly returned `"DE"`).
- [x] `update_cheer_aggregations()` correctly counts the current month's
      cheer log and publishes `cheers_aggregations.json` — verified by
      running it directly against production: 3 real cheers in
      `cheers/2026-07.json` → `{"month": "2026-07", "count": 3}`.
- [x] Two near-simultaneous cheer submissions both land in `cheers/<YYYY-MM>.json`
      (no lost writes) — user-tested 2026-07-06, confirmed working.
- [x] After cheering once in a browser, the button shows "Thanks for the
      support! 🎉" and re-cheering is blocked client-side until
      `localStorage` is cleared, or the calendar month rolls over —
      user-tested 2026-07-06, confirmed working. (The monthly-expiry fix
      landed after the initial user test: the original version stored a bare
      `"true"` flag with no expiry at all, which would have permanently
      blocked repeat monthly visitors — caught before shipping further.)
- [x] `run_intraday()` on the actual Raspberry Pi cron picks up
      `update_cheer_aggregations()` and keeps `cheers_aggregations.json`
      fresh hourly in real operation — confirmed 2026-07-06 10:00 CEST: a
      fully automatic (not manually triggered) cron tick uploaded
      `today.json`, `activities.json`, and `cheers_aggregations.json`
      together (`{"month": "2026-07", "count": 10}`).

## Deployment steps
- [x] **Frontend** — push to `main` → GitHub Actions auto-builds & deploys to
      GitHub Pages / wandern-eric.de (existing pipeline, unchanged).
- [x] **Cloud Function** — deployed, project `codineric`, region
      `europe-west10` (matches the bucket's location), gen2, Python 3.12,
      `--max-instances=1 --concurrency=1`, `--allow-unauthenticated`.
      Runtime identity: `cheer-function@codineric.iam.gserviceaccount.com`,
      IAM-conditioned to the `cheers/` prefix only in `wandern-eric-data`.
      Build identity: a separate
      `cheer-function-build@codineric.iam.gserviceaccount.com` (needed
      because the project had zero pre-existing service accounts, including
      the default Compute Engine one Cloud Build normally uses — worked
      around with an explicit `--build-service-account` rather than chasing
      the missing default). Live URL:
      `https://europe-west10-codineric.cloudfunctions.net/cheer`.
      ⚠️ Redeploy needed any time `cheer-function/main.py` changes — not
      automatic, no CI hooked up.
- [x] `CHEER_ENDPOINT` in `lib/config.js` set to the live URL above.
      **Deliberately kept the `import.meta.env.DEV` mock gate** in
      `lib/cheerApi.js` — without it, `npm run dev` would POST real cheers to
      production on every test click. Only production builds hit the live
      function; local dev still uses the mock.
- [x] **Production server (RasPi)** — `python-backend/main.py` (with
      `update_cheer_aggregations()` + `GCP_CHEERS_AGG_BLOB_NAME`) uploaded to
      the Pi 2026-07-06 (diffed, backed up the old version, `scp`'d, confirmed
      it imports cleanly in the Pi's own poetry env). Since confirmed running
      for real via the actual hourly cron — see acceptance criteria above.
- [x] **GCS schema** — new objects only; no existing keys (`data.json`,
      `aggregations.json`) touched, so `Heatmap.jsx`/`Aggregations.jsx` need
      no changes.
- [x] Update `Changelog.jsx` (user-facing change).

## Open questions
(none — resolved during spec discussion. Country display, BMC API queries,
and Patreon integration are deliberate *deferrals*, not open questions — see
Out of scope.)
