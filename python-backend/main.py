from requests_oauthlib import OAuth2Session
from google.cloud import storage
from pathlib import Path
from dotenv import load_dotenv
import datetime
import webbrowser
import os
import json
import pandas as pd


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
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
    data_str = data_bytes.decode('utf-8')
    data = json.loads(data_str)
    return data

# GCP logic
def upload_file_to_gcp(bucket_name, destination_blob_name, local_path):
    project = os.getenv("GCP_PROJECT_ID")
    storage_client = storage.Client(project=project)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(local_path)

    print(f"Uploaded file {local_path} → gs://{bucket_name}/{destination_blob_name}")


def calculate_aggregations(data_path: Path):
    df = pd.read_json(data_path)
    df['date'] = pd.to_datetime(df['date'])


    aggregations = {}

    # Day with the highest count
    max_count = df[df['count'].max() == df['count']]
    # date to string
    max_count['date'] = max_count['date'].dt.strftime('%Y-%m-%d')
    aggregations["max_steps"] = max_count[["date", "count"]].to_dict(orient='records')[0]

    # Max AVG Day of the week
    df['day_of_week'] = df['date'].dt.day_name()
    avg_by_day = df.groupby('day_of_week').agg({
        'count': 'mean',
    }).reset_index()
    aggregations["max_avg_dow"] = avg_by_day[avg_by_day['count'].max() == avg_by_day['count']].to_dict(orient='records')[0]

    # avg per month
    df['month'] = df['date'].dt.month_name()
    avg_by_month = df.groupby('month').agg({
        'count': 'mean',
    }).reset_index()
    aggregations['avg_per_month'] = avg_by_month.to_dict(orient='records')

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

        return response.json()

    def __get_session(self):
        # load token
        if TOKEN_PATH.exists():
            with open(TOKEN_PATH) as f:
                saved_token = json.load(f)

            if saved_token:
                # check token is not expired
                if saved_token['expires_at'] <= datetime.datetime.now().timestamp():
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
        fitbit = OAuth2Session(
            CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPES
        )

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
        resp = self.session.get(f"https://api.fitbit.com/1/user/-/activities/date/{date_str}.json")
        if resp.status_code != 200:
            raise ValueError(f"Error fetching data: {resp.status_code} - {resp.text}")
        steps = resp.json()['summary']['steps']
        sedentary_mins = resp.json()['summary']['sedentaryMinutes']

        record = {'date': yesterday_str, 'count': steps, 'sedentary_minutes': sedentary_mins}
        return record 


if __name__ == "__main__":
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    print(f"Fetching data for: {yesterday_str}")

    # Get data from fitbit
    fitbit_controller = FitbitController()
    record = fitbit_controller.get_daily_steps(yesterday_str)
    print(f"Fetched data: {record}")

    # download from GCP
    bucket_name = os.getenv("GCP_BUCKET_NAME")
    destination_blob_name = 'data.json'
    data = get_file_from_gcp(bucket_name, destination_blob_name)
    
    if data is None:
        raise ValueError("Failed to load data from GCP")
    
    data.append(record)

    # save locally
    data_path = ROOT_DIR / "data.json"
    with open(data_path, "w") as f:
        json.dump(data, f)
    
    # aggregations
    aggregations = calculate_aggregations(data_path)

    # save locally
    agg_path = ROOT_DIR / "aggregations.json"

    with open(agg_path, "w") as f:
        json.dump(aggregations, f)

    # upload to GCP
    upload_file_to_gcp(bucket_name, destination_blob_name, str(data_path))
    upload_file_to_gcp(bucket_name, 'aggregations.json', str(agg_path))
