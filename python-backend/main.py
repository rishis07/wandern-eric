from requests_oauthlib import OAuth2Session
from google.cloud import storage
from pathlib import Path
from dotenv import load_dotenv
import datetime
import webbrowser
import os
import json


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
load_dotenv()

# Replace with your Fitbit app details
CLIENT_ID = os.getenv("CLIENT_ID") 
CLIENT_SECRET = os.getenv("CLIENT_SECRET")  
REDIRECT_URI = os.getenv("REDIRECT_URI") 

AUTH_BASE_URL = os.getenv("AUTH_BASE_URL") 
AUTH_URL = os.getenv("AUTH_URL") 
TOKEN_URL = os.getenv("TOKEN_URL")

# Scopes determine what data you can read
SCOPES = ["activity", "cardio_fitness", "location", "heartrate", "sleep", "profile"]

# GCP logic
def upload_file_to_gcp(bucket_name, destination_blob_name, local_path):
    project = os.getenv("GCP_PROJECT_ID")
    storage_client = storage.Client(project=project)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(local_path)

    print(f"Uploaded file {local_path} → gs://{bucket_name}/{destination_blob_name}")

def save_token(token):
    with open("token.json", "w") as f:
        json.dump(token, f)


def load_token():
    if os.path.exists("token.json"):
        with open("token.json") as f:
            return json.load(f)
    return None


def get_fitbit_session():
    saved_token = load_token()

    # If we have a token already — use it (it will auto-refresh)
    if saved_token:
        return OAuth2Session(
            CLIENT_ID,
            token=saved_token,
            auto_refresh_url=TOKEN_URL,
            auto_refresh_kwargs={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
            token_updater=save_token,
        )

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

    save_token(token)
    return fitbit


if __name__ == "__main__":
    fitbit = get_fitbit_session()

    # yesterday
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    print(f"Fetching data for: {yesterday_str}")
    
    resp = fitbit.get(f"https://api.fitbit.com/1/user/-/activities/date/{yesterday_str}.json")
    steps = resp.json()['summary']['steps']
    sedentary_mins = resp.json()['summary']['sedentaryMinutes']

    record = {'date': yesterday_str, 'count': steps, 'sedentary_minutes': sedentary_mins}

    # update data.json file with the new record
    ROOT_DIR = Path(__file__).parent.parent.resolve()

    data_path = ROOT_DIR / 'wandern-eric/src/data/data.json'

    if data_path.exists():
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        # data.append(record)

        with open(ROOT_DIR / 'wandern-eric/src/data2.json', 'w') as f:
            json.dump(data, f, indent=4)
        
        # upload to GCP
        bucket_name = os.getenv("GCP_BUCKET_NAME")
        destination_blob_name = 'data.json'
        upload_file_to_gcp(bucket_name, destination_blob_name, str(data_path))

    else:
        print(f"{data_path} does not exist.")
