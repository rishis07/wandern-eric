from requests_oauthlib import OAuth2Session
from google.cloud import storage
from pathlib import Path
from dotenv import load_dotenv
import datetime
from calendar import monthrange
import webbrowser
import os
import json
import argparse
import pandas as pd

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
load_dotenv()

ROOT_DIR = Path(__file__).parent
TOKEN_PATH = ROOT_DIR / "token.json"

# Replace with your Fitbit app details
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

AUTH_BASE_URL = os.getenv("AUTH_BASE_URL")
AUTH_URL = os.getenv("AUTH_URL")
TOKEN_URL = os.getenv("TOKEN_URL")


# GCP config
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
GCP_DATA_BLOB_NAME = "data.json"
GCP_AGG_BLOB_NAME = "aggregations.json"
GCP_TODAY_BLOB_NAME = "today.json"

# Scopes determine what data you can read
SCOPES = ["activity", "cardio_fitness", "location", "heartrate", "sleep", "profile"]


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


class FitbitController:
    def __init__(self):
        self.session = self.__get_session()

    def __save_token(self, token):
        token["expires_at"] = datetime.datetime.now().timestamp() + token["expires_in"]
        with open(TOKEN_PATH, "w") as f:
            json.dump(token, f)

    def __get_refresh_token(self, token):
        import requests
        import base64

        url = "https://api.fitbit.com/oauth2/token"

        auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
        auth_header = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data_request = {
            "grant_type": "refresh_token",
            "client_id": f"{CLIENT_ID}",
            "refresh_token": f'{token["refresh_token"]}',
        }

        response = requests.post(url, headers=headers, data=data_request)
        refreshed = response.json()

        # Fitbit returns an error payload (no access_token) when the refresh
        # token is invalid. Fail clearly instead of crashing later with a
        # cryptic KeyError on token["expires_in"].
        if response.status_code != 200 or "access_token" not in refreshed:
            detail = (
                refreshed.get("errors")
                or refreshed.get("error_description")
                or refreshed.get("error")
                or "unknown error"
            )
            raise RuntimeError(
                f"Fitbit token refresh failed (HTTP {response.status_code}): {detail}."
            )

        return refreshed

    def __get_session(self):
        # load token
        if TOKEN_PATH.exists():
            with open(TOKEN_PATH) as f:
                saved_token = json.load(f)

            if saved_token:
                # check token is not expired
                if saved_token["expires_at"] <= datetime.datetime.now().timestamp():
                    print("Token expired, refreshing...")
                    saved_token = self.__get_refresh_token(saved_token)
                    self.__save_token(saved_token)
                    print("Token refreshed.")

                client = OAuth2Session(
                    CLIENT_ID,
                    token=saved_token,
                    auto_refresh_url=TOKEN_URL,
                    auto_refresh_kwargs={
                        "client_id": CLIENT_ID,
                        "client_secret": CLIENT_SECRET,
                    },
                    token_updater=self.__save_token,
                )

                return client

        # First-time authorization
        fitbit = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPES)

        authorization_url, state = fitbit.authorization_url(AUTH_URL)
        print("Open this URL to authorize:", authorization_url)
        webbrowser.open(authorization_url)

        redirect_response = input("Paste full redirect URL: ")

        token = fitbit.fetch_token(
            TOKEN_URL,
            client_secret=CLIENT_SECRET,
            authorization_response=redirect_response,
        )

        # save token
        self.__save_token(token)

        return fitbit

    def get_daily_steps(self, date_str):
        resp = self.session.get(
            f"https://api.fitbit.com/1/user/-/activities/date/{date_str}.json"
        )
        if resp.status_code != 200:
            raise ValueError(f"Error fetching data: {resp.status_code} - {resp.text}")
        steps = resp.json()["summary"]["steps"]
        sedentary_mins = resp.json()["summary"]["sedentaryMinutes"]

        record = {
            "date": date_str,
            "count": steps,
            "sedentary_minutes": sedentary_mins,
        }
        return record


def update_and_save_fitbit_data(data_path: Path, date_str: str):
    fitbit_controller = FitbitController()
    record = fitbit_controller.get_daily_steps(date_str)
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

    # Get data from fitbit
    update_and_save_fitbit_data(data_path, yesterday_str)

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
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    print(f"[intraday] Fetching in-progress data for: {today_str}")

    controller = FitbitController()
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
    parser = argparse.ArgumentParser(description="Wandern Eric Fitbit extractor")
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
