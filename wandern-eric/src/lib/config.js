// App configuration. Non-sensitive and committed to the repo, so it's baked into
// the build (nothing to set on GitHub Pages). To run your own instance, edit the
// values here and commit. See README > Run your own.

// The public GCS bucket that holds the JSON data files.
export const GCS_BUCKET = "wandern-eric-data";

export const DATA_BASE_URL = `https://storage.googleapis.com/${GCS_BUCKET}`;

export const CHEERS_AGGREGATIONS_URL = `${DATA_BASE_URL}/cheers_aggregations.json`;

export const CHEER_ENDPOINT = "https://europe-west10-codineric.cloudfunctions.net/cheer";

export const BUY_ME_A_COFFEE_URL = "https://buymeacoffee.com/wanderneric";
