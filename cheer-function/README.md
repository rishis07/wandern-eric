# cheer-function

The `POST /cheer` Cloud Function from `specs/0006-cheer-button.md`. Appends a
cheer event (`{timestamp, country}`) to `cheers/<YYYY-MM>.json` (one file per
calendar month) in the `wandern-eric-data` bucket. Country comes from
geolocating the request IP via ipapi.co; the raw IP itself is never
persisted. This function only appends — the monthly count
(`cheers_aggregations.json`) is computed separately, by
`python-backend/main.py`'s `update_cheer_aggregations()`, hooked into the
existing hourly `run_intraday()` cron.

**Live deployment:** project `codineric`, region `europe-west10`, URL
`https://europe-west10-codineric.cloudfunctions.net/cheer`.

## Local setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run locally
```bash
GCP_PROJECT_ID=<your-project> GCP_BUCKET_NAME=wandern-eric-data \
  functions-framework --target=cheer --debug
```

## Deploy
⚠️ Manual — not part of any CI pipeline. Re-run this any time `main.py` changes.

```bash
gcloud functions deploy cheer \
  --gen2 \
  --runtime=python312 \
  --region=europe-west10 \
  --source=. \
  --entry-point=cheer \
  --trigger-http \
  --allow-unauthenticated \
  --max-instances=1 \
  --concurrency=1 \
  --set-env-vars=GCP_PROJECT_ID=codineric,GCP_BUCKET_NAME=wandern-eric-data \
  --service-account=cheer-function@codineric.iam.gserviceaccount.com \
  --build-service-account=projects/codineric/serviceAccounts/cheer-function-build@codineric.iam.gserviceaccount.com \
  --project=codineric
```

- `--max-instances=1 --concurrency=1` serializes every invocation globally, so
  only one request ever runs at a time — this is what makes concurrent
  cheers safe, on top of the generation-match retry loop in `_append_cheer`
  (belt-and-suspenders: the retry loop stays even though this config alone
  would prevent the race, in case the flags are ever dropped in a future
  redeploy).
- The runtime service account (`cheer-function@codineric.iam.gserviceaccount.com`)
  has `roles/storage.objectAdmin` on the bucket, IAM-conditioned to only the
  `cheers/` prefix (`resource.name.startsWith(".../objects/cheers/")`) — not
  full bucket admin, and not scoped to a single file, since the blob name now
  varies by month.
- The build service account (`cheer-function-build@codineric.iam.gserviceaccount.com`)
  exists only because this project had no default Compute Engine service
  account for Cloud Build to use — it needs
  `roles/cloudbuild.builds.builder`, `roles/artifactregistry.writer`,
  `roles/logging.logWriter`, `roles/storage.objectViewer` at the project
  level.
- `CHEER_ENDPOINT` in `wandern-eric/wandern-eric/src/lib/config.js` is already
  set to the live URL above. The `import.meta.env.DEV` mock gate in
  `lib/cheerApi.js` was deliberately kept (not deleted) so local `npm run dev`
  never posts real cheers to production.
