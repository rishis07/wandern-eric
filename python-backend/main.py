from google.cloud import storage
from google.auth.transport.requests import AuthorizedSession, Request
import google.oauth2.credentials
import google_auth_oauthlib.flow
from pathlib import Path
from dotenv import load_dotenv
import datetime
from calendar import monthrange
import os
import json
import argparse
import pandas as pd

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
load_dotenv()

ROOT_DIR = Path(__file__).parent

# GCP config
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
GCP_DATA_BLOB_NAME = "data.json"
GCP_AGG_BLOB_NAME = "aggregations.json"
GCP_TODAY_BLOB_NAME = "today.json"

# Google Health API config (server-to-server successor to the Fitbit Web API)
HEALTH_BASE_URL = "https://health.googleapis.com/v4"
HEALTH_SCOPES = ["https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly"]
HEALTH_CLIENT_SECRET_PATH = ROOT_DIR / "secrets/client_secret_health.json"
HEALTH_TOKEN_PATH = ROOT_DIR / "secrets/token_health.json"


def get_file_from_gcp(bucket_name, blob_name):
    project = os.getenv("GCP_PROJECT_ID")
    storage_client = storage.Client(project=project)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    if not blob.exists():
        return []

    data_bytes = blob.download_as_bytes()
    data_str = data_bytes.decode("utf-8")
    data = json.loads(data_str)
    return data


# GCP logic
def upload_file_to_gcp(bucket_name, destination_blob_name, local_path, cache_control=None):
    project = os.getenv("GCP_PROJECT_ID")
    storage_client = storage.Client(project=project)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # today.json updates hourly; no-cache stops GCS edge caching from masking it
    if cache_control is not None:
        blob.cache_control = cache_control

    blob.upload_from_filename(local_path)

    print(f"Uploaded file {local_path} → gs://{bucket_name}/{destination_blob_name}")


def calculate_aggregations(data_path: Path):
    df = pd.read_json(data_path)
    df["date"] = pd.to_datetime(df["date"])

    # Filter current month
    today = datetime.datetime.today() - pd.Timedelta(days=1)  # today is not over yet
    current_month = today.month
    current_year = today.year

    aggregations = {}

    # Day with the highest count
    max_count = df[df["count"].max() == df["count"]]
    # date to string
    max_count = max_count.copy()
    max_count["date"] = max_count["date"].dt.strftime("%Y-%m-%d")
    aggregations["max_steps"] = max_count[["date", "count"]].to_dict(orient="records")[
        0
    ]

    # Max AVG Day of the week
    df["day_of_week"] = df["date"].dt.day_name()
    avg_by_day = (
        df.groupby("day_of_week")
        .agg(
            {
                "count": "mean",
            }
        )
        .reset_index()
    )
    aggregations["max_avg_dow"] = avg_by_day[
        avg_by_day["count"].max() == avg_by_day["count"]
    ].to_dict(orient="records")[0]

    # avg per month
    df["month_num"] = df["date"].dt.month
    df["month"] = df["date"].dt.month_name()
    df["year"] = df["date"].dt.year

    avg_by_month = (
        df.groupby(["year", "month", "month_num"], as_index=False)
        .agg({"count": "mean"})
        .sort_values(["year", "month_num"])
    )

    avg_by_month["count"] = avg_by_month["count"].astype(int)

    aggregations["avg_per_month"] = avg_by_month.to_dict(orient="records")

    # avg last 3 months
    aggregations["avg_last_3_months"] = (
        avg_by_month.sort_values(["year", "month_num"], ascending=[False, False])
        .head(3)
        .to_dict(orient="records")
    )

    # steps per day needed to continue last month avg
    df_current = df[
        (df["date"].dt.month == current_month) & (df["date"].dt.year == current_year)
    ]

    # Steps so far this month
    steps_so_far = df_current["count"].sum()

    # Days passed
    days_passed = today.day

    # Days in this month
    days_in_month = monthrange(current_year, current_month)[1]
    days_left = days_in_month - days_passed

    # get avg of prev month
    prev_month = current_month - 1 if current_month > 1 else 12
    prev_year = current_year if current_month > 1 else current_year - 1

    avg_prev = avg_by_month[
        (
            avg_by_month["month"]
            == datetime.datetime(prev_year, prev_month, 1).strftime("%B")
        )
        & (avg_by_month["year"] == prev_year)
    ]["count"].values[0]

    # ---- Required totals ----
    required_total_steps = avg_prev * days_in_month
    remaining_steps = required_total_steps - steps_so_far

    if days_left <= 0:
        steps_per_day_needed = 0
    else:
        steps_per_day_needed = remaining_steps / days_left

    aggregations["prev_month_avg_to_eom_projection"] = {
        "last_month": int(avg_prev),
        "current_month": int(steps_per_day_needed),
    }

    return aggregations


class GoogleHealthController:
    """Reads daily steps from the Google Health API.

    Replaces the old Fitbit Web API integration. get_daily_steps(date_str)
    keeps the same {date, count} contract the rest of the pipeline expects.
    """

    def __init__(self):
        self.session = self.__get_session()

    def __save_token(self, creds):
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
        }
        HEALTH_TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(HEALTH_TOKEN_PATH, "w") as f:
            json.dump(token_data, f)

    def __get_session(self):
        creds = None

        if HEALTH_TOKEN_PATH.exists():
            with open(HEALTH_TOKEN_PATH) as f:
                token_data = json.load(f)
            creds = google.oauth2.credentials.Credentials(
                token=token_data.get("token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri=token_data.get("token_uri"),
                client_id=token_data.get("client_id"),
                client_secret=token_data.get("client_secret"),
                scopes=HEALTH_SCOPES,
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Token expired, refreshing...")
                creds.refresh(Request())
                print("Token refreshed.")
            else:
                # First-time authorization (needs a browser).
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                    str(HEALTH_CLIENT_SECRET_PATH), scopes=HEALTH_SCOPES
                )
                creds = flow.run_local_server(port=8080)
            self.__save_token(creds)

        # AuthorizedSession refreshes the access token automatically per request.
        return AuthorizedSession(creds)

    @staticmethod
    def __civil(d):
        """Google Health CivilDateTime for the start of a day (local time)."""
        return {
            "date": {"year": d.year, "month": d.month, "day": d.day},
            "time": {"hours": 0, "minutes": 0},
        }

    def get_daily_steps(self, date_str):
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

        url = f"{HEALTH_BASE_URL}/users/me/dataTypes/steps/dataPoints:dailyRollUp"
        body = {
            "range": {
                "start": self.__civil(date),
                "end": self.__civil(date + datetime.timedelta(days=1)),
            },
            "windowSizeDays": 1,
        }

        resp = self.session.post(
            url, json=body, headers={"Accept": "application/json"}
        )
        if resp.status_code != 200:
            raise ValueError(f"Error fetching data: {resp.status_code} - {resp.text}")

        steps = 0
        for rp in resp.json().get("rollupDataPoints", []):
            steps += int(rp.get("steps", {}).get("countSum", 0))

        record = {
            "date": date_str,
            "count": steps,
        }
        return record


def update_and_save_data(data_path: Path, date_str: str):
    controller = GoogleHealthController()
    record = controller.get_daily_steps(date_str)
    print(f"Fetched data: {record}")

    # download from GCP
    data = get_file_from_gcp(GCP_BUCKET_NAME, GCP_DATA_BLOB_NAME)

    if data is None:
        raise ValueError("Failed to load data from GCP")

    data.append(record)

    # save locally
    with open(data_path, "w") as f:
        json.dump(data, f)


def run_daily():
    """Finalize yesterday into data.json, recompute aggregations, upload both.

    Meant for the 1am cron run.
    """
    data_path = ROOT_DIR / "data.json"
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")

    print(f"[daily] Fetching finalized data for: {yesterday_str}")

    # Get data from the Google Health API
    update_and_save_data(data_path, yesterday_str)

    # aggregations
    aggregations = calculate_aggregations(data_path)

    # save locally
    agg_path = ROOT_DIR / "aggregations.json"

    with open(agg_path, "w") as f:
        json.dump(aggregations, f)

    # upload to GCP
    upload_file_to_gcp(GCP_BUCKET_NAME, GCP_DATA_BLOB_NAME, str(data_path))
    upload_file_to_gcp(GCP_BUCKET_NAME, GCP_AGG_BLOB_NAME, str(agg_path))


def run_intraday():
    """Fetch today's in-progress steps and overwrite today.json. No aggregations.

    Meant for the hourly cron run (8am–11pm). today.json holds a single record.
    """
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    print(f"[intraday] {now:%Y-%m-%d %H:%M} Fetching in-progress data for: {today_str}")

    controller = GoogleHealthController()
    record = controller.get_daily_steps(today_str)
    record["intraday"] = True  # flags the day as still in progress

    today_path = ROOT_DIR / "today.json"
    with open(today_path, "w") as f:
        json.dump(record, f)

    upload_file_to_gcp(
        GCP_BUCKET_NAME,
        GCP_TODAY_BLOB_NAME,
        str(today_path),
        cache_control="no-cache, max-age=0",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wandern Eric step extractor (Google Health API)")
    parser.add_argument(
        "--intraday",
        action="store_true",
        help="Fetch today's in-progress steps to today.json and skip aggregations "
        "(hourly run). Default finalizes yesterday + recomputes aggregations (1am run).",
    )
    args = parser.parse_args()

    if args.intraday:
        run_intraday()
    else:
        run_daily()
