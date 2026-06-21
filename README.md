# Wandern Eric
Wandern Eric is a front end pet project to force Eric to walk.

Hi, my name is Eric and I spend 10 to 12 hours a day sitting on my desk, Doctors might say that this is not helty but
I dont really have a reason to get up.
Wandern Eric connects my watch data with a nice UI so I can keep track of how bad my sedentary life is affecting me.


## Migrate to Google Health
To ensure a seamless experience for your users, we recommend waiting until the end of May 2026 to officially launch your integration to align with legacy Fitbit account deprecation. Please be aware that from now until the end of May, breaking changes may occur as we respond to developer feedback.

https://developers.google.com/health/migration

## Architecture
### Frontend
I asked twitter for ideas and I got 100 options. I asked chatGePeTo and told me to use REACT + Tailwind with vite.
It's a little of an overkill but the most basic thing I wanted was the GH heatmap which I found as a REACT lib

### Backend
Currently Python extraction. I extracted the historical data manually and transform it with Pandas.

## Future ideas
- Automate daily extraction.
- Add challenges.

## Backlog / known issues
- **Daily append is not idempotent (low priority).** `update_and_save_data` in
  `python-backend/main.py` appends the day's record to `data.json` without checking
  whether that date already exists, so running the daily job twice for the same date
  creates a duplicate record that has to be deleted by hand. Easy fix: replace-or-insert
  by `date` (drop any existing record for that date before appending) so re-runs are safe.